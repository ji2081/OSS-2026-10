.PHONY: up down restart logs psql reset

up:
	docker compose up -d

down:
	docker compose down

restart:
	docker compose down && docker compose up -d

logs:
	docker compose logs -f db

psql:
	docker exec -it youth_policy_db psql -U policy_admin -d youth_policy

reset:
	docker compose down -v
	docker compose up -d

seed-check:
	docker exec -it youth_policy_db psql -U policy_admin -d youth_policy \
		-c "SELECT code, name, category, confidence FROM policies ORDER BY code;"

graph-check:
	docker exec -it youth_policy_db psql -U policy_admin -d youth_policy \
		-c "SELECT * FROM v_policy_graph;"

summary:
	docker exec -it youth_policy_db psql -U policy_admin -d youth_policy \
		-c "SELECT * FROM v_eligible_summary;"
