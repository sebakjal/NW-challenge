from google.cloud import bigquery
import pandas as pd


def csv_from_cs_to_bq(event, context):
    # Se inicializa un cliente de BigQuery
    client = bigquery.Client()

    # Se inicializan variables estáticas
    bucket_name = 'nw-upload'
    project = 'neuralwork-challenge'
    dataset = 'cities'

    # Contiene los datos del "evento" que activó el trigger (en este caso, un archivo .csv)
    csv_file = event['name']

    # Se transforma el .csv subido a un dataframe de pandas
    cities_df = pd.read_csv('gs://{}/{}'.format(bucket_name, csv_file))

    # Se inician las configuraciones para el trabajo de carga a BigQuery
    job_config = bigquery.LoadJobConfig(
        schema=[
            bigquery.SchemaField("region", "STRING"),
            bigquery.SchemaField("timestamp", "TIMESTAMP"),
            bigquery.SchemaField("hora", "INTEGER"),
            bigquery.SchemaField("origin_cell", "STRING"),
            bigquery.SchemaField("destination_cell", "STRING"),
            bigquery.SchemaField("origin_x", "FLOAT"),
            bigquery.SchemaField("origin_y", "FLOAT"),
            bigquery.SchemaField("destination_x", "FLOAT"),
            bigquery.SchemaField("destination_y", "FLOAT"),
            bigquery.SchemaField("datasource", "STRING")
        ],

        source_format=bigquery.SourceFormat.CSV,
        write_disposition=bigquery.WriteDisposition().WRITE_APPEND,

        # Configuración de particiones de la tabla
        range_partitioning=bigquery.RangePartitioning(
            field="hora",
            range_=bigquery.PartitionRange(start=0, end=24, interval=1)
        ),
    )

    # Se obtienen los nombres de regiones únicas desde el dataframe
    cities = cities_df['region'].unique()

    # Para cada región única se crea un dataframe temporal con las filas de esa región, se sube a la tabla correspondiente y se imprime a LOGS la cantidad de filas cargadas
    for city in cities:
        dataframe = cities_df[cities_df['region'] == city]
        table_id = '{}.{}.{}'.format(project, dataset, city.lower())

        load_job = client.load_table_from_dataframe(
            dataframe, table_id, job_config=job_config
        )

        load_job.result()
        print("Loaded {} rows into the {} table.".format(str(load_job.output_rows), city.lower()))

    return 'Check the results in the logs'