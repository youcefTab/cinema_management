import logging
from typing import Any

from django.core.management.base import BaseCommand, CommandParser
from django.db import transaction

from core.models import Film, ProductionCompany
from core.tmdb_integration.tmdb_client import TMDBClient, TMDBClientError

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Commande Django pour importer des films depuis l'API TMDb.
    Exemple :
        python manage.py import_tmdb_movies --pages 2
    """

    help = "Importe les films populaires depuis TMDb et met à jour la base de données."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--pages",
            type=int,
            default=1,
            help="Nombre de pages de films populaires à importer depuis TMDb (par défaut: 1).",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        page_count = options["pages"]
        self.stdout.write(
            self.style.NOTICE(
                f"Import TMDb : récupération des {page_count} pages de films..."
            )
        )

        client = TMDBClient()
        imported_count = 0
        updated_count = 0
        company_count = 0

        try:
            movies = client.get_popular_movies(page_count=page_count)
            logger.info(
                "TMDb import : %d films trouvés sur %d pages", len(movies), page_count
            )
            self.stdout.write(
                self.style.NOTICE(
                    f"{len(movies)} films trouvés sur {page_count} pages."
                )
            )

            for movie_data in movies:
                tmdb_id = movie_data.get("id")
                if not tmdb_id:
                    continue

                try:
                    self.stdout.write(
                        self.style.NOTICE(f"Import du film TMDb ID {tmdb_id}...")
                    )
                    details = client.get_movie_details(tmdb_id)
                    if not details:
                        logger.info(
                            "Détails non trouvés pour le film TMDb ID %s", tmdb_id
                        )
                        continue

                    with transaction.atomic():
                        film, created = Film.objects.update_or_create(
                            tmdb_id=details["id"],
                            defaults={
                                "titre": details.get("title") or "",
                                "titre_original": details.get("original_title") or "",
                                "overview": details.get("overview") or "",
                                "release_date": details.get("release_date") or None,
                                "runtime": details.get("runtime"),
                                "poster_path": details.get("poster_path") or "",
                                "backdrop_path": details.get("backdrop_path") or "",
                                "vote_average": details.get("vote_average"),
                                "vote_count": details.get("vote_count"),
                                "popularity": details.get("popularity"),
                                "original_language": details.get("original_language")
                                or "",
                                "adult": details.get("adult", False),
                                "statut": details.get("status", "n/a") or "n/a",
                                "created_via_tmdb": True,
                            },
                        )

                        self.stdout.write(
                            self.style.SUCCESS(
                                f"Film '{film.titre}' (TMDb ID {tmdb_id}) {'créé' if created else 'mis à jour'}."
                            )
                        )

                        if created:
                            imported_count += 1
                        else:
                            updated_count += 1

                        # Gestion des production_companies
                        companies = details.get("production_companies", [])
                        logger.info(
                            "Traitement de %d companies pour le film TMDb ID %s",
                            len(companies),
                            tmdb_id,
                        )
                        for c in companies:
                            company, _ = ProductionCompany.objects.update_or_create(
                                tmdb_id=c.get("id"),
                                defaults={
                                    "name": c.get("name", ""),
                                    "logo_path": c.get("logo_path", "") or "",
                                    "origin_country": c.get("origin_country", "") or "",
                                    "source": "TMDB",
                                },
                            )
                            film.production_companies.add(company)
                            company_count += 1
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f"  Company liée : '{company.name}' (TMDb ID {company.tmdb_id})"
                                )
                            )
                            logger.info(
                                "Company liée : '%s' (TMDb ID %s)",
                                company.name,
                                company.tmdb_id,
                            )
                except TMDBClientError as e:
                    logger.error("Erreur TMDb pour le film ID %s : %s", tmdb_id, e)
                    continue

            self.stdout.write(
                self.style.SUCCESS(
                    f"**>> Import terminé : {imported_count} nouveaux films, {updated_count} mis à jour, {company_count} companies liées."
                )
            )

        except TMDBClientError as e:
            logger.error("Erreur TMDb client : %s", e)
            self.stderr.write(self.style.ERROR(f"Erreur TMDb client : {e}"))

        except Exception as e:
            logger.exception("Erreur inattendue durant l'import TMDb")
            self.stderr.write(self.style.ERROR(f"Erreur inattendue : {e}"))

        finally:
            client.close()
            self.stdout.write(self.style.NOTICE("Connexion TMDb fermée."))
