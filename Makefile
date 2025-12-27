.PHONY: add commit push build clean clear clear-pycache clear-ruff clear-pytest

add:
	git add .

commit: add
	git commit -m "$(msg)"

push: commit
	git push

build:
	docker compose down -v || true
	docker compose up --build

clean:
	docker compose down -v || true
	docker system prune -af --volumes
	docker image prune -af
	docker volume prune -af

clear-pycache:
	find . -type d -name '__pycache__' -exec rm -rf {} +

clear-ruff: clear-pycache
	find . -type d -name '.ruff_cache' -exec rm -rf {} +

clear-pytest: clear-ruff
	find . -type d -name '.pytest_cache' -exec rm -rf {} +

clear: clear-pytest
	clear
