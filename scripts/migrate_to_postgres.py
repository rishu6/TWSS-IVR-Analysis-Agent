"""Copy a consistent private Mac backup into a dedicated empty cloud database.

Never logs row values or the destination URL. Existing cloud customer data is
never overwritten. The service must remain in MIGRATION_PENDING setup mode.
"""
import os
import hashlib
import json
import sys
from pathlib import Path
from sqlalchemy import create_engine,select,func,Integer,JSON,text,delete

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app.db import Base,Call,Lead,User
from app.maintenance import backup
from app.credentials import read_env


def migrate(source_path,destination_url,progress=False):
    if destination_url.startswith('postgresql://'):destination_url=destination_url.replace('postgresql://','postgresql+psycopg://',1)
    if destination_url.startswith('postgres://'):destination_url=destination_url.replace('postgres://','postgresql+psycopg://',1)
    if not destination_url.startswith('postgresql+psycopg://'):raise ValueError('A PostgreSQL destination is required')
    source=create_engine('sqlite:///'+str(Path(source_path).resolve()))
    target=create_engine(destination_url,pool_pre_ping=True)
    counts={};skip={'sessions','live_tickets'}
    try:
        with source.connect() as src,target.begin() as dst:
            if dst.scalar(select(func.count()).select_from(Call)) or dst.scalar(select(func.count()).select_from(Lead)):
                raise ValueError('Destination already contains customer records; import refused')
            users=dst.execute(select(User.username)).scalars().all()
            if users and users!=['localadmin']:raise ValueError('Destination has staff accounts; import refused')
            if not src.execute(select(User.id).where(User.role=='Admin',User.active==True)).first():
                raise ValueError('Source has no active administrator')
            dst.execute(text("SET TIME ZONE 'UTC'"))
            for table in reversed(Base.metadata.sorted_tables):dst.execute(delete(table))
            for table in Base.metadata.sorted_tables:
                if table.name in skip:counts[table.name]=0;continue
                from psycopg import sql
                from psycopg.types.json import Json
                count=0;result=src.execute(select(table)).mappings()
                if progress:print({'copying_table':table.name},flush=True)
                command=sql.SQL('COPY {} ({}) FROM STDIN').format(sql.Identifier(table.name),
                    sql.SQL(',').join(sql.Identifier(column.name) for column in table.c))
                with dst.connection.driver_connection.cursor() as cursor:
                    with cursor.copy(command) as copy:
                        while True:
                            batch=result.fetchmany(5000)
                            if not batch:break
                            for row in batch:
                                copy.write_row(tuple(Json(row[column.name]) if isinstance(column.type,JSON)
                                    and not (row[column.name] is None and column.type.none_as_null)
                                    else row[column.name] for column in table.c))
                            count+=len(batch)
                            if progress and count%10000==0:print({'table':table.name,'rows_copied':count},flush=True)
                actual=dst.scalar(select(func.count()).select_from(table))
                if actual!=count:raise ValueError('Imported table count mismatch')
                counts[table.name]=count
                column=table.c.get('id')
                if column is not None and isinstance(column.type,Integer) and column.primary_key:
                    maximum=dst.scalar(select(func.max(column))) or 0
                    dst.execute(text('SELECT setval(pg_get_serial_sequence(:table_name, :column_name), :value, :used)'),
                        {'table_name':table.name,'column_name':'id','value':max(1,maximum),'used':bool(maximum)})
        return counts
    finally:source.dispose();target.dispose()


if __name__=='__main__':
    os.umask(0o077)
    path=ROOT/'.runtime/render/migration-source.db'
    if not path.exists():backup(ROOT/'.runtime/internal.db',path)
    settings=read_env(ROOT/'.env.render')
    try:
        result=migrate(path,settings['DATABASE_URL'],progress=True)
        proof={'database_fingerprint':hashlib.sha256(settings['DATABASE_URL'].encode()).hexdigest(),'table_counts':result}
        target=ROOT/'.runtime/render/migration-verified.json'
        target.write_text(json.dumps(proof));target.chmod(0o600)
        print({'migration':'complete','table_counts':result})
    except Exception as exc:
        # Connection exceptions can contain credentials; never display raw errors.
        print({'migration':'failed','error_type':type(exc).__name__,'sqlstate':getattr(getattr(exc,'orig',None),'sqlstate',None)});raise SystemExit(1)
