.PHONY: build clean

build:
	docker compose down -v || true
	docker compose up --build

clean:
	docker compose down -v || true
	docker system prune -af --volumes
	docker image prune -af
	docker volume prune -af
