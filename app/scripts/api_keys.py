import argparse
import os
import sys
import json
from datetime import datetime
from app.db.session import SessionLocal, engine
from app.stores.sql_api_keys import SqlApiKeyStore
from app.security.api_keys import get_pepper

def iso(dt):
    if not dt:
        return None
    return dt.isoformat()

def main():
    parser = argparse.ArgumentParser(description="Manage project API keys (DB store)")
    parser.add_argument("--database-url", help="Database URL (overrides env DATABASE_URL)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_create = subparsers.add_parser("create", help="Create a new API key")
    p_create.add_argument("--project-id", required=True)
    p_create.add_argument("--name")

    p_list = subparsers.add_parser("list", help="List API keys for a project")
    p_list.add_argument("--project-id", required=True)

    p_revoke = subparsers.add_parser("revoke", help="Revoke an API key")
    p_revoke.add_argument("--project-id", required=True)
    p_revoke.add_argument("--key-id", required=True)

    args = parser.parse_args()

    # Set up DB
    if args.database_url:
        os.environ["DATABASE_URL"] = args.database_url
    try:
        pepper = get_pepper()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(2)
    try:
        db = SessionLocal()
        store = SqlApiKeyStore(db)
    except Exception as e:
        print(f"ERROR: Could not connect to DB: {e}", file=sys.stderr)
        sys.exit(2)

    try:
        if args.command == "create":
            raw_key, rec = store.create(args.project_id, args.name)
            out = {
                "api_key": raw_key,
                "api_key_id": rec.id,
                "key_prefix": rec.key_prefix,
                "name": rec.name,
                "created_at": iso(rec.created_at)
            }
            if args.json:
                print(json.dumps(out, indent=2))
            else:
                print("\n*** API KEY CREATED ***")
                print(f"RAW API KEY (save now!): {raw_key}")
                print("This key will NOT be shown again. Store it securely.\n")
                print(f"api_key_id: {rec.id}")
                print(f"key_prefix: {rec.key_prefix}")
                print(f"name: {rec.name}")
                print(f"created_at: {iso(rec.created_at)}")
        elif args.command == "list":
            keys = store.list(args.project_id)
            if args.json:
                print(json.dumps([
                    {
                        "api_key_id": k.id,
                        "key_prefix": k.key_prefix,
                        "name": k.name,
                        "created_at": iso(k.created_at),
                        "last_used_at": iso(k.last_used_at),
                        "revoked_at": iso(k.revoked_at)
                    } for k in keys
                ], indent=2))
            else:
                print(f"API keys for project {args.project_id}:")
                for k in keys:
                    print(f"- id: {k.id}  prefix: {k.key_prefix}  name: {k.name}  created: {iso(k.created_at)}  last_used: {iso(k.last_used_at)}  revoked: {iso(k.revoked_at)}")
        elif args.command == "revoke":
            rec = store.revoke(args.project_id, args.key_id)
            if not rec:
                print(f"ERROR: API key not found for project {args.project_id} and id {args.key_id}", file=sys.stderr)
                sys.exit(1)
            out = {"api_key_id": rec.id, "revoked_at": iso(rec.revoked_at)}
            if args.json:
                print(json.dumps(out, indent=2))
            else:
                if rec.revoked_at:
                    print(f"API key {rec.id} revoked at {iso(rec.revoked_at)}")
                else:
                    print(f"API key {rec.id} was already revoked at {iso(rec.revoked_at)}")
        else:
            parser.print_help()
            sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()
