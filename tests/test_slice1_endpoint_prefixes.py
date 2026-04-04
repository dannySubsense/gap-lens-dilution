"""
Slice 1: Endpoint Prefix Fix + Config Tests

Acceptance Criteria Coverage:
- [x] AC (config): Default askedgar_url is "https://eapi.askedgar.io"
- [x] AC (news): get_news uses /enterprise/v1/news prefix
- [x] AC (registrations): get_registrations uses /enterprise/v1/registrations prefix
- [x] AC (dilution-data): get_dilution_detail uses /enterprise/v1/dilution-data prefix
- [x] AC (dilution-rating): _make_request for dilution-rating uses /enterprise/v1/ prefix
- [x] AC (float-outstanding): _make_request for float-outstanding uses /enterprise/v1/ prefix
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
from app.services.dilution import DilutionService
from app.core.config import Settings


class TestDefaultConfig:
    """Verify default configuration values for the AskEdgar base URL."""

    def test_default_askedgar_url_is_eapi(self):
        """Default askedgar_url must be https://eapi.askedgar.io (not a /v1/ sub-path)."""
        settings = Settings()
        assert settings.askedgar_url == "https://eapi.askedgar.io"


class TestEndpointPrefixes:
    """Verify all AskEdgar HTTP calls use the correct /enterprise/v1/ prefix."""

    def _make_service_with_mock_client(self):
        """Return a DilutionService with its httpx client replaced by a MagicMock."""
        service = DilutionService()
        mock_client = AsyncMock()
        # Default: return a 200 response with an empty results list
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": [{}]}
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        service.client = mock_client
        return service, mock_client

    @pytest.mark.asyncio
    async def test_news_endpoint_uses_enterprise_v1_prefix(self):
        """get_news must call /enterprise/v1/news."""
        service, mock_client = self._make_service_with_mock_client()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": []}
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        await service.get_news("EEIQ")

        mock_client.get.assert_called_once()
        called_url = mock_client.get.call_args[0][0]
        assert "/enterprise/v1/news" in called_url, (
            f"Expected /enterprise/v1/news in URL, got: {called_url}"
        )

    @pytest.mark.asyncio
    async def test_registrations_endpoint_uses_enterprise_v1_prefix(self):
        """get_registrations must call /enterprise/v1/registrations."""
        service, mock_client = self._make_service_with_mock_client()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": []}
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        await service.get_registrations("EEIQ")

        mock_client.get.assert_called_once()
        called_url = mock_client.get.call_args[0][0]
        assert "/enterprise/v1/registrations" in called_url, (
            f"Expected /enterprise/v1/registrations in URL, got: {called_url}"
        )

    @pytest.mark.asyncio
    async def test_dilution_detail_endpoint_uses_enterprise_v1_prefix(self):
        """get_dilution_detail must call /enterprise/v1/dilution-data."""
        service, mock_client = self._make_service_with_mock_client()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": []}
        mock_response.raise_for_status = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        await service.get_dilution_detail("EEIQ")

        mock_client.get.assert_called_once()
        called_url = mock_client.get.call_args[0][0]
        assert "/enterprise/v1/dilution-data" in called_url, (
            f"Expected /enterprise/v1/dilution-data in URL, got: {called_url}"
        )

    @pytest.mark.asyncio
    async def test_dilution_rating_call_uses_enterprise_v1_prefix(self):
        """get_dilution_data must call dilution-rating under /enterprise/v1/."""
        service, mock_client = self._make_service_with_mock_client()

        # Five concurrent calls in get_dilution_data: dilution-rating, float-outstanding,
        # news (_make_request_list), registrations (_make_request_list), dilution-data (_make_request_list)
        def make_ok_response(results_value):
            r = MagicMock()
            r.status_code = 200
            r.json.return_value = {"results": results_value}
            r.raise_for_status = MagicMock()
            return r

        mock_client.get = AsyncMock(side_effect=[
            make_ok_response([{}]),   # dilution-rating
            make_ok_response([{}]),   # float-outstanding
            make_ok_response([]),     # news
            make_ok_response([]),     # registrations
            make_ok_response([]),     # dilution-data
        ])

        await service.get_dilution_data("EEIQ")

        all_urls = [c[0][0] for c in mock_client.get.call_args_list]
        dilution_rating_urls = [u for u in all_urls if "dilution-rating" in u]
        assert len(dilution_rating_urls) == 1, (
            f"Expected one dilution-rating call, found: {dilution_rating_urls}"
        )
        assert "/enterprise/v1/dilution-rating" in dilution_rating_urls[0], (
            f"Expected /enterprise/v1/ prefix, got: {dilution_rating_urls[0]}"
        )

    @pytest.mark.asyncio
    async def test_float_outstanding_call_uses_enterprise_v1_prefix(self):
        """get_dilution_data must call float-outstanding under /enterprise/v1/."""
        service, mock_client = self._make_service_with_mock_client()

        def make_ok_response(results_value):
            r = MagicMock()
            r.status_code = 200
            r.json.return_value = {"results": results_value}
            r.raise_for_status = MagicMock()
            return r

        mock_client.get = AsyncMock(side_effect=[
            make_ok_response([{}]),   # dilution-rating
            make_ok_response([{}]),   # float-outstanding
            make_ok_response([]),     # news
            make_ok_response([]),     # registrations
            make_ok_response([]),     # dilution-data
        ])

        await service.get_dilution_data("EEIQ")

        all_urls = [c[0][0] for c in mock_client.get.call_args_list]
        float_urls = [u for u in all_urls if "float-outstanding" in u]
        assert len(float_urls) == 1, (
            f"Expected one float-outstanding call, found: {float_urls}"
        )
        assert "/enterprise/v1/float-outstanding" in float_urls[0], (
            f"Expected /enterprise/v1/ prefix, got: {float_urls[0]}"
        )

    @pytest.mark.asyncio
    async def test_all_five_calls_use_enterprise_v1_prefix(self):
        """All 5 AskEdgar calls in get_dilution_data must use /enterprise/v1/ prefix."""
        service, mock_client = self._make_service_with_mock_client()

        def make_ok_response(results_value):
            r = MagicMock()
            r.status_code = 200
            r.json.return_value = {"results": results_value}
            r.raise_for_status = MagicMock()
            return r

        mock_client.get = AsyncMock(side_effect=[
            make_ok_response([{}]),   # dilution-rating
            make_ok_response([{}]),   # float-outstanding
            make_ok_response([]),     # news
            make_ok_response([]),     # registrations
            make_ok_response([]),     # dilution-data
        ])

        await service.get_dilution_data("EEIQ")

        assert mock_client.get.call_count == 5, (
            f"Expected 5 AskEdgar calls, got {mock_client.get.call_count}"
        )
        all_urls = [c[0][0] for c in mock_client.get.call_args_list]
        for url in all_urls:
            assert "/enterprise/v1/" in url, (
                f"URL missing /enterprise/v1/ prefix: {url}"
            )
