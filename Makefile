makemigrations:
	docker compose run --rm cinema-backend poetry run python manage.py makemigrations
migrate:
	docker compose run --rm cinema-backend poetry run python manage.py migrate
superuser:
	docker compose run --rm cinema-backend poetry run python manage.py createsuperuser
test-project:
	docker compose run --rm cinema-backend poetry run pytest .
test-users:
	docker compose run --rm cinema-backend poetry run pytest users/tests
test-core:
	docker compose run --rm cinema-backend poetry run pytest core/tests
import-tmdb:
	docker compose run --rm cinema-backend poetry run python manage.py import_tmdb_movies --pages=$(pages)
shell:
	docker compose exec cinema-backend bash
