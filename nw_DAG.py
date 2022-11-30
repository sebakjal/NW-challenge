import datetime
import os
import pendulum
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.providers.papermill.operators.papermill import PapermillOperator


# Seteo de variables
home_path = os.path.expanduser('~')
working_path = home_path + '/neuralworks/'
owner = 'owner'
gcs_bucket = 'nw-upload'

# Cambio al directorio de trabajo o creación de este si no existe
if os.path.isdir(working_path):
    os.chdir(working_path)
else:
    os.mkdir(working_path)
    os.chdir(working_path)

# DAG principal
# La primera task corre todas las celdas del notebook de python usando el operador de papermill
# La segunda task espera 300 segundos para asegurarse que todos los .csv hayan sido procesados
# La tercera task carga los datos del .csv condensado diario al bucket de cloud storage

default_args = {
    'owner': owner,
    'email_on_failure': False}

with DAG(
        dag_id='trips_upload',
        default_args=default_args,
        schedule='* 20 * * *',  # equivalente a las 17:00 hora Chile continental
        start_date=pendulum.datetime(2022, 1, 1, tz="UTC"),
        catchup=False,
        dagrun_timeout=datetime.timedelta(minutes=60),
        tags=['nw_challenge']
) as dag:

    process_csv = PapermillOperator(
        task_id='process_csv',
        input_nb=working_path + 'csv_process.ipynb',
        output_nb=working_path + 'test_nb.ipynb',
        parameters={}
    )

    sleep_300 = BashOperator(
        task_id='sleep_300',
        bash_command='sleep 300'
    )

    gcs_load = BashOperator(
        task_id='gcs_load',
        bash_command='gsutil cp -n {}upload/formatted_trips.csv gs://{}'.format(working_path, gcs_bucket)
    )

    process_csv >> sleep_300 >> gcs_load

if __name__ == "__main__":
    dag.cli()