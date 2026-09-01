.PHONY: publish res check package-deps mac-app mac-dmg windows-exe windows-installer

ifneq (,$(wildcard .env))
include .env
export
endif

publish:
	@echo "Building and publishing package..."
	@test -n "$$PYPI_TOKEN" || (echo "PYPI_TOKEN is required. Add it to .env or export it." && exit 1)
	@uv build && \
	uv publish --token $$PYPI_TOKEN

res:
	@echo "Building app resources file..."
	@cd scripts && sh generate_resources_file.sh

check:
	@uv run python -m compileall src tests

package-deps:
	@if [ ! -f deps/modihub/pyproject.toml ]; then git submodule update --init --recursive; fi
	@uv sync

mac-app: package-deps
	@uv run --with pyinstaller pyinstaller packaging/pyinstaller/quack2tex.spec --noconfirm --clean

mac-dmg: mac-app
	@sh packaging/macos/build-dmg.sh

windows-exe: package-deps
	@uv run --with pyinstaller pyinstaller packaging/pyinstaller/quack2tex.spec --noconfirm --clean

windows-installer: windows-exe
	@ISCC packaging/windows/installer.iss
