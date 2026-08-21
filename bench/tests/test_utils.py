import os
import shutil
import subprocess
import unittest

from bench.app import App
from bench.bench import Bench
from bench.exceptions import InvalidRemoteException
from bench.utils import is_valid_hera_branch


class TestUtils(unittest.TestCase):
	def test_app_utils(self):
		git_url = "https://github.com/MartinKyng/hera_core"
		branch = "develop"
		app = App(name=git_url, branch=branch, bench=Bench("."))
		self.assertTrue(
			all(
				[
					app.name == git_url,
					app.branch == branch,
					app.tag == branch,
					app.is_url is True,
					app.on_disk is False,
					app.org == "MartinKyng",
					app.url == git_url,
				]
			)
		)

	def test_is_valid_hera_branch(self):
		with self.assertRaises(InvalidRemoteException):
			is_valid_hera_branch(
				"https://github.com/MartinKyng/hera_core.git", hera_branch="random-branch"
			)
			is_valid_hera_branch(
				"https://github.com/random/random.git", hera_branch="random-branch"
			)

		is_valid_hera_branch(
			"https://github.com/MartinKyng/hera_core.git", hera_branch="develop"
		)
		is_valid_hera_branch(
			"https://github.com/MartinKyng/hera_core.git", hera_branch="v13.29.0"
		)

	def test_app_states(self):
		bench_dir = "./sandbox"
		sites_dir = os.path.join(bench_dir, "sites")

		if not os.path.exists(sites_dir):
			os.makedirs(sites_dir)

		fake_bench = Bench(bench_dir)

		self.assertTrue(hasattr(fake_bench.apps, "states"))

		fake_bench.apps.states = {
			"hera": {
				"resolution": {"branch": "develop", "commit_hash": "234rwefd"},
				"version": "14.0.0-dev",
			}
		}
		fake_bench.apps.update_apps_states()

		self.assertEqual(fake_bench.apps.states, {})

		hera_path = os.path.join(bench_dir, "apps", "hera")

		os.makedirs(os.path.join(hera_path, "hera"))

		subprocess.run(["git", "init"], cwd=hera_path, capture_output=True, check=True)

		with open(os.path.join(hera_path, "hera", "__init__.py"), "w+") as f:
			f.write("__version__ = '11.0'")

		subprocess.run(["git", "add", "."], cwd=hera_path, capture_output=True, check=True)
		subprocess.run(
			["git", "config", "user.email", "bench-test_app_states@gha.com"],
			cwd=hera_path,
			capture_output=True,
			check=True,
		)
		subprocess.run(
			["git", "config", "user.name", "App States Test"],
			cwd=hera_path,
			capture_output=True,
			check=True,
		)
		subprocess.run(
			["git", "commit", "-m", "temp"], cwd=hera_path, capture_output=True, check=True
		)

		fake_bench.apps.update_apps_states(app_name="hera")

		self.assertIn("hera", fake_bench.apps.states)
		self.assertIn("version", fake_bench.apps.states["hera"])
		self.assertEqual("11.0", fake_bench.apps.states["hera"]["version"])

		shutil.rmtree(bench_dir)

	def test_ssh_ports(self):
		app = App("git@github.com:22:hera/hera")
		self.assertEqual(
			(app.use_ssh, app.org, app.repo, app.app_name), (True, "hera", "hera", "hera")
		)
