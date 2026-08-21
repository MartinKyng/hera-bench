VERSION = "1.0.0"
PROJECT_NAME = "hera-bench"
HERA_VERSION = None
current_path = None
updated_path = None
LOG_BUFFER = []


def set_hera_version(bench_path="."):
	from .utils.app import get_current_hera_version

	global HERA_VERSION
	if not HERA_VERSION:
		HERA_VERSION = get_current_hera_version(bench_path=bench_path)
