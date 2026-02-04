"""Tests for CameraSource."""

from unittest.mock import MagicMock, patch, PropertyMock

import numpy as np
import pytest

from pyrheed.video.camera import CameraSource, enumerate_cameras
from pyrheed.video.source import SourceState


@pytest.fixture
def mock_camera():
    """Create a mock camera that returns test frames."""
    with patch("pyrheed.video.camera.cv2.VideoCapture") as mock_cap_class:
        # Create mock capture instance
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: {
            0: 640.0,   # CAP_PROP_FRAME_WIDTH (cv2.CAP_PROP_POS_FRAMES)
            1: 480.0,   # CAP_PROP_FRAME_HEIGHT
            3: 640.0,   # CAP_PROP_FRAME_WIDTH
            4: 480.0,   # CAP_PROP_FRAME_HEIGHT
            5: 30.0,    # CAP_PROP_FPS
            10: 128.0,  # CAP_PROP_BRIGHTNESS
            11: 100.0,  # CAP_PROP_CONTRAST
            15: -6.0,   # CAP_PROP_EXPOSURE
        }.get(prop, 0.0)
        mock_cap.getBackendName.return_value = "MOCK"

        # Return test frame
        test_frame = np.full((480, 640, 3), 128, dtype=np.uint8)
        mock_cap.read.return_value = (True, test_frame)

        mock_cap_class.return_value = mock_cap

        yield mock_cap


class TestCameraSource:
    """Tests for CameraSource."""

    def test_open_valid_device(self, mock_camera):
        """open() should succeed with valid device ID."""
        source = CameraSource()
        result = source.open("0")

        assert result is True
        assert source.fps == 30.0

        source.close()

    def test_open_invalid_device_id(self):
        """open() should fail for invalid device ID string."""
        source = CameraSource()

        # Non-numeric string
        result = source.open("invalid")
        assert result is False

    def test_open_unavailable_device(self):
        """open() should fail for unavailable device."""
        with patch("pyrheed.video.camera.cv2.VideoCapture") as mock_cap_class:
            mock_cap = MagicMock()
            mock_cap.isOpened.return_value = False
            mock_cap_class.return_value = mock_cap

            source = CameraSource()
            result = source.open("99")

            assert result is False

    def test_is_live(self, mock_camera):
        """CameraSource should report as live source."""
        source = CameraSource()
        source.open("0")

        assert source.is_live is True

        source.close()

    def test_total_frames_is_zero(self, mock_camera):
        """Live source should have 0 total frames."""
        source = CameraSource()
        source.open("0")

        assert source.total_frames == 0

        source.close()

    def test_get_frame(self, mock_camera):
        """get_frame() should return current camera frame."""
        source = CameraSource()
        source.open("0")

        frame = source.get_frame(0)  # Index ignored for live source

        assert frame is not None
        assert frame.shape == (480, 640)
        assert frame.dtype == np.uint8

        source.close()

    def test_seek_not_supported(self, mock_camera):
        """seek() should return False for live source."""
        source = CameraSource()
        source.open("0")

        result = source.seek(10)

        assert result is False

        source.close()

    def test_get_camera_info(self, mock_camera):
        """get_camera_info() should return camera properties."""
        source = CameraSource()
        source.open("0")

        info = source.get_camera_info()

        assert info["device_id"] == 0
        assert info["width"] == 640
        assert info["height"] == 480
        assert info["fps"] == 30.0
        assert info["backend"] == "MOCK"

        source.close()

    def test_set_resolution(self, mock_camera):
        """set_resolution() should update camera resolution."""
        mock_camera.set.return_value = True
        # Make get() return the new values after set
        mock_camera.get.side_effect = lambda prop: {
            3: 1280.0,  # CAP_PROP_FRAME_WIDTH
            4: 720.0,   # CAP_PROP_FRAME_HEIGHT
            5: 30.0,
        }.get(prop, 0.0)

        source = CameraSource()
        source.open("0")

        result = source.set_resolution(1280, 720)

        assert result is True

        source.close()

    def test_set_exposure(self, mock_camera):
        """set_exposure() should update camera exposure."""
        mock_camera.set.return_value = True

        source = CameraSource()
        source.open("0")

        result = source.set_exposure(-5.0)

        assert result is True
        mock_camera.set.assert_called()

        source.close()

    def test_set_brightness(self, mock_camera):
        """set_brightness() should update camera brightness."""
        mock_camera.set.return_value = True

        source = CameraSource()
        source.open("0")

        result = source.set_brightness(150)

        assert result is True

        source.close()

    def test_close(self, mock_camera):
        """close() should release camera resources."""
        source = CameraSource()
        source.open("0")

        source.close()

        assert source.state == SourceState.STOPPED
        mock_camera.release.assert_called_once()

    def test_error_signal_on_invalid_id(self, qtbot):
        """ERROR_OCCURRED should be emitted for invalid device ID."""
        source = CameraSource()

        with qtbot.waitSignal(source.ERROR_OCCURRED, timeout=1000) as blocker:
            source.open("not_a_number")

        assert "Invalid device ID" in blocker.args[0]

    def test_start_without_open(self, qtbot):
        """start() without open() should emit error."""
        source = CameraSource()

        with qtbot.waitSignal(source.ERROR_OCCURRED, timeout=1000) as blocker:
            source.start()

        assert "No camera opened" in blocker.args[0]

    def test_pause_stops_camera(self, mock_camera):
        """pause() should stop the camera (no pause for live)."""
        source = CameraSource()
        source.open("0")

        # Mock the worker
        source._worker = MagicMock()
        source._worker.isRunning.return_value = True
        source._state = SourceState.PLAYING

        source.pause()

        assert source.state == SourceState.STOPPED

        source.close()


class TestEnumerateCameras:
    """Tests for enumerate_cameras function."""

    def test_enumerate_no_cameras(self):
        """Should return empty list when no cameras available."""
        with patch("pyrheed.video.camera.cv2.VideoCapture") as mock_cap_class:
            mock_cap = MagicMock()
            mock_cap.isOpened.return_value = False
            mock_cap_class.return_value = mock_cap

            devices = enumerate_cameras(max_devices=3)

            assert devices == []

    def test_enumerate_with_cameras(self):
        """Should return list of available cameras."""
        with patch("pyrheed.video.camera.cv2.VideoCapture") as mock_cap_class:
            def create_mock(device_id):
                mock = MagicMock()
                # Only device 0 and 1 are available
                mock.isOpened.return_value = device_id < 2
                mock.getBackendName.return_value = "V4L2"
                return mock

            mock_cap_class.side_effect = create_mock

            devices = enumerate_cameras(max_devices=5)

            assert len(devices) == 2
            assert devices[0]["id"] == 0
            assert devices[0]["available"] is True
            assert "V4L2" in devices[0]["name"]
            assert devices[1]["id"] == 1
