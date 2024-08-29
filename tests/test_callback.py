import pytest

import consul
from consul.base import Response
from consul.callback import CB
from consul.exceptions import ACLDisabled, ACLPermissionDenied, BadRequest, ClientError, NotFound


class TestCB:
    # pylint: disable=protected-access
    def test_status_200_passes(self) -> None:
        response = consul.base.Response(200, None, None)
        CB._status(response)

    @pytest.mark.parametrize(
        ("response", "expected_exception"),
        [
            (Response(400, None, None), BadRequest),
            (Response(401, None, None), ACLDisabled),
            (Response(403, None, None), ACLPermissionDenied),
        ],
    )
    def test_status_4xx_raises_error(self, response, expected_exception) -> None:
        with pytest.raises(expected_exception):
            CB._status(response)

    def test_status_404_allow_404(self) -> None:
        response = Response(404, None, None)
        CB._status(response, allow_404=True)

    def test_status_404_dont_allow_404(self) -> None:
        response = Response(404, None, None)
        with pytest.raises(NotFound):
            CB._status(response, allow_404=False)

    def test_status_405_raises_generic_ClientError(self) -> None:
        response = Response(405, None, None)
        with pytest.raises(ClientError):
            CB._status(response)

    @pytest.mark.parametrize(
        "response",
        [
            Response(500, None, None),
            Response(599, None, None),
        ],
    )
    def test_status_5xx_raises_error(self, response) -> None:
        with pytest.raises(consul.base.ConsulException):
            CB._status(response)
