.PHONY: publish res

publish:
	@echo "Building and publishing package..."
	@export $(shell grep -v '^#' .env | xargs) && \
	uv build && \
	uv publish --token $$PYPI_TOKEN
res:
	@echo "Building app resources file..."
	@export $(shell grep -v '^#' .env | xargs) && \
    cd scripts && sh generate_resources_file.sh