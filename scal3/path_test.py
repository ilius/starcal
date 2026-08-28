from os.path import join

from scal3.path import APP_NAME, confDir, tmpDir


def test_confDir_is_temporary() -> None:
	assert confDir == join(tmpDir, APP_NAME)
