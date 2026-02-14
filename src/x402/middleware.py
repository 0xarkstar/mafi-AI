"""X402 payment middleware for FastAPI."""

from __future__ import annotations

import structlog
from decimal import Decimal
from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from src.config.settings import Settings
from src.x402.models import X402PaymentInfo

logger = structlog.get_logger()


class X402Middleware(BaseHTTPMiddleware):
    """
    Middleware to enforce X402 payment requirements on specific routes.

    Protects routes that require USDC payment via X402 protocol.
    If x402_enabled=False, middleware is a no-op passthrough.
    """

    def __init__(
        self,
        app: ASGIApp,
        settings: Settings,
        protected_paths: list[str] | None = None,
    ):
        """
        Initialize X402 middleware.

        Args:
            app: ASGI application
            settings: Application settings
            protected_paths: List of URL paths to protect (default: ["/api/bets/x402"])
        """
        super().__init__(app)
        self.settings = settings
        self.protected_paths = protected_paths or ["/api/bets"]
        self.enabled = settings.x402_enabled

        # Only initialize x402 server if enabled
        self.x402_server = None
        if self.enabled:
            try:
                from x402 import FacilitatorClient
                from x402.server import x402ResourceServer

                # Create facilitator client
                facilitator_client = FacilitatorClient(
                    facilitator_url=settings.x402_facilitator_url,
                )

                # Create x402 resource server
                self.x402_server = x402ResourceServer(
                    facilitator_clients=facilitator_client,
                )

                # Register USDC payment scheme for Monad testnet
                # Network format: eip155:10143 (Monad testnet Chain ID)
                from x402 import Network, Money, AssetAmount

                self.x402_server.register(
                    method="POST",
                    route_pattern="/api/bets",
                    payment_requirements=[
                        {
                            "network": Network(settings.x402_network),
                            "accepted_assets": [
                                AssetAmount(
                                    asset=Money(
                                        contract=settings.x402_usdc_address,
                                        decimals=6,  # USDC has 6 decimals
                                    ),
                                    amount=1_000_000,  # 1 USDC minimum (1e6 smallest units)
                                )
                            ],
                            "payTo": settings.x402_pay_to,
                        }
                    ],
                )

                logger.info(
                    "x402_middleware_initialized",
                    protected_paths=self.protected_paths,
                    facilitator_url=settings.x402_facilitator_url,
                    network=settings.x402_network,
                )
            except ImportError as e:
                logger.error("x402_import_failed", error=str(e))
                self.enabled = False
            except Exception as e:
                logger.error("x402_initialization_failed", error=str(e))
                self.enabled = False

    async def dispatch(self, request: Request, call_next):
        """
        Process request and enforce X402 payment if required.

        Args:
            request: FastAPI request
            call_next: Next middleware/route handler

        Returns:
            Response with payment requirement or successful response
        """
        # If x402 is disabled, return 503 Service Unavailable for protected paths
        if not self.enabled:
            path = request.url.path
            if any(path.startswith(protected) for protected in self.protected_paths):
                if request.method == "POST":
                    return Response(
                        content="X402 betting is not enabled",
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    )
            return await call_next(request)

        # Check if this path requires payment
        path = request.url.path
        if not any(path.startswith(protected) for protected in self.protected_paths):
            return await call_next(request)

        # Only enforce on POST requests
        if request.method != "POST":
            return await call_next(request)

        try:
            # Check for x-payment header
            payment_header = request.headers.get("x-payment")

            if not payment_header:
                # No payment provided - return 402 Payment Required
                logger.info("x402_payment_required", path=path)

                # Create payment requirements response
                payment_required_response = await self.x402_server.create_payment_required_response(
                    method="POST",
                    url=str(request.url),
                )

                return Response(
                    content=payment_required_response.body,
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    headers=dict(payment_required_response.headers),
                )

            # Verify payment
            verify_result = await self.x402_server.verify_payment(
                method="POST",
                url=str(request.url),
                headers=dict(request.headers),
            )

            if not verify_result:
                logger.warning("x402_verification_failed", path=path)
                return Response(
                    content="Payment verification failed",
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                )

            # Extract payment info from verified result
            # The verify_result contains the payment payload with transaction details
            payment_payload = verify_result.payload

            # Extract relevant fields from payment payload
            # Assuming payload has payer address and amount
            payer_address = payment_payload.get("from", "unknown")
            amount_raw = payment_payload.get("amount", 0)
            tx_hash = payment_payload.get("txHash", "unknown")

            # Convert amount from smallest units (1e6) to USDC (Decimal)
            amount_usdc = Decimal(amount_raw) / Decimal(1_000_000)

            # Create payment info and attach to request state
            payment_info = X402PaymentInfo(
                payer_address=payer_address,
                amount_usdc=amount_usdc,
                tx_hash=tx_hash,
            )

            request.state.x402_payment = payment_info

            logger.info(
                "x402_payment_verified",
                path=path,
                payer=payer_address,
                amount=str(amount_usdc),
                tx_hash=tx_hash,
            )

            # Settle payment after successful verification
            await self.x402_server.settle_payment(
                method="POST",
                url=str(request.url),
                headers=dict(request.headers),
            )

            return await call_next(request)

        except Exception as e:
            logger.error("x402_middleware_error", error=str(e), path=path)
            return Response(
                content=f"Payment processing error: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


def create_x402_middleware(settings: Settings):
    """
    Factory function to create X402Middleware instance.

    Args:
        settings: Application settings

    Returns:
        X402Middleware class configured with settings
    """
    def middleware_factory(app: ASGIApp):
        return X402Middleware(app, settings)

    return middleware_factory
