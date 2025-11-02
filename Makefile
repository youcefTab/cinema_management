makemigrations:
	docker compose run --rm cinema-backend poetry run python manage.py makemigrations
migrate:
	docker compose run --rm cinema-backend poetry run python manage.py migrate
test-project:
	docker compose run --rm cinema-backend poetry run pytest .
test-users:
	docker compose run --rm cinema-backend poetry run pytest users/tests
shell:
	docker compose exec cinema-backend bash
