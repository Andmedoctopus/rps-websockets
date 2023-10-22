PROJECT_CODE_PATH=/code/

.PHONY: format-black
format-black:
	docker compose run --rm app sh -c "black ${PROJECT_CODE_PATH}"

.PHONY: fix-imports
fix-imports:
	docker compose run --rm app sh -c "autoflake -r --in-place --ignore-init-module-imports --remove-all-unused-imports ${PROJECT_CODE_PATH} && isort ${PROJECT_CODE_PATH}"

.PHONY: format
format: format-black fix-imports

.PHONY: lint
lint: flake8 import-check format-check

.PHONY: flake8
flake8:
	docker compose run --rm app flake8 ${PROJECT_CODE_PATH}

.PHONY: import-check
import-check:
	docker compose run --rm app sh -c "isort --check ${PROJECT_CODE_PATH}"

.PHONY: format-check
format-check:
	docker compose run --rm app sh -c "black --check ${PROJECT_CODE_PATH}"

.PHONY: tests
tests:
	docker compose run --rm app sh -c "pytest"

.PHONY: run
run:
	docker compose up --build
