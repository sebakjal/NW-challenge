# Challenge de Neuralworks

El challenge consiste en crear un proyecto de ingesta de datos que toma los datos desde un .csv, los agrupe según ciertas características y los suba a una base de datos para que luego puedan ser utilizados para análisis posteriores. En estos primeros párrafos se explica como se realiza la solución, luego se responden las preguntas en específico.

## Diagrama de flujo de datos

![Diagrama de flujo](https://github.com/sebakjal/NW_challenge/blob/main/imagenes/NWchallenge%20flow.png)

Tecnologías usadas:

- Python
- Google Cloud Storage
- Google Cloud Functions
- Google Cloud BigQuery
- Airflow

El flujo de los datos comienza una carpeta local, donde se tienen el notebook de Python y el(los) archivos .csv con datos de viajes que los usuarios han puesto. Una vez al día Airflow corre el notebook de Python, que contiene el código para limpiar y formatear los datos, dejando como resultado un archivo .csv. De la misma forma, Airlfow toma este archivo resultante y lo sube a un bucket de Cloud Storage. Al subir un archivo se activa un trigger de Cloud Functions, que toma el nuevo archivo y lo separa por región, mandando los datos a tablas separadas de BigQuery, siendo esta la base de datos SQL. 

## Solución

Para desarrollar la solución se pide que los viajes tienen que estar agrupados por similitud, tanto por distancia como por tiempo. Por simplicidad, y dado que se trata de un ejercicio hipotético, se asume en esta solución que la cercanía por distancia se refiere a que estén en la misma región, que una persona no tenga que caminar más allá de unos 700m. y que la simlitud por tiempo sea dentro de la misma hora (13:01 y 13:59 son la misma hora en este caso). Se usan diferentes soluciones para cada uno de los requerimientos.

### Región
En el caso de la región, dado que es una separación muy grande en distancia y los viajes están contenidos dentro de esta misma, se opta por separar los datos en tablas diferentes. Es decir, una tabla para cada región.

![Tablas](https://github.com/sebakjal/NW_challenge/blob/main/imagenes/BQTables.png)

### Horario
Para la similitud por hora se decide crear una columna que contenga la hora en forma de número entero. Esto significa que un viaje realizado a las 15:27 tiene una columna con el valor 15. Esto se hace para que sea simple realizar una query agrupando los datos con valores de tiempo similares. Adicionalmente, las tablas se particionan por esta misma columna, haciendo más eficiente las consultas a BigQuery y permitiendo la visualización de coste más precisa. Esto se hace en anticipo a un aumento grande en la cantidad de registros.

![Particion](https://github.com/sebakjal/NW_challenge/blob/main/imagenes/BQPartitions.png)

Una forma de mejorar esta solución es agregando también la división por minutos. 

### Cercanía
En cuanto a la cercanía dentro de una misma región, para hacer una agrupamiento se hace una división geoespacial de la región de estudio en una grilla de celdas, con coordenadas combinadas entre letras y números, imitando en cierta manera el proceso división del sistema de coordenadas proyectadas global, pero a nivel más local. Para la división se usan cuadrantes de 1000m. de lado, que asumiendo que los pasajeros se toman en el medio del cuadrante, significa que el pasajero más lejano tiene que caminar unos 700m.
El eje X se indica con números enteros que van aumentando hacia el este, y el eje Y se indica con letras, que van aumentando hacia el norte (ver Imagen). Para las celdas más allá de la letra "Z" se sigue el formato de Microsoft Excel, donde las celdas toman valores en el estilo "AB", "AC", "AD", etc.
Con este método es muy fácil identificar las zonas con mayor concentración de viajes y hacer otros análisis.

![Grilla](https://github.com/sebakjal/NW_challenge/blob/main/imagenes/GrillaNeuralWorksTurin.png)

Una forma de mejorar esta solución es disminuir el tamaño del cuadrante, usando una división mas fina que permita reducir el tiempo en caminar hacia el punto de encuentro.

## Preguntas específicas

1. Procesos automatizados para ingerir y almacenar los datos bajo demanda
a. Los viajes que son similares en términos de origen, destino y hora del día deben agruparse. Describa el enfoque que utilizó para agregar viajes similares.

El proceso de automatización de ingestión de datos bajo demanda viene dado por la herramienta de Airflow y Cloud Functions. Airflow se encarga de correr el código todos los días a la misma hora, recogiendo todos los archivos con información que se hayan subido a la carpeta del proyecto y la sube a la nube. Mientras tanto, Cloud Functions contiene la función con un trigger automático que toma la información limpia y la manda hacia BigQuery. Queda abierta la opción de realizar todo el procesamiento de datos dentro de Cloud Functions, prescindiendo de un entero local.

La parte de almacenamiento se hace usando Cloud Storage y BigQuery. Cloud Storage guarda los .csv que vienen con datos limpios, mientras que BigQuery se usa como destino final de los datos, al actuar como la base de datos SQL sobre la que se hacen los análisis y/o modelos.

El proceso para agrupar viajes similares ya se explicó anteriormente en la solución general.

2. Un servicio que es capaz de proporcionar la siguiente funcionalidad:

a. Devuelve el promedio semanal de la cantidad de viajes para un área definida por un bounding box y la región

Dado que se tiene la columna con la fecha completa con el tipo TIMESTAMP de BigQuery, se pueden hacer queries en cualquier espacio temporal, incluyendo semanal. La región está dada simplemente por hacer la consulta a la tabla correspondiente. Por último, se puede hacer una query a una bounding box usando los comandos BETWEEN y aprovechando las coordenadas geográficas. En la imagen se observa un ejemplo de este tipo de query. x1, x2, y1 y y2 se pueden reemplazar por los límites de la bounding box.

![Query con límites](https://github.com/sebakjal/NW_challenge/blob/main/imagenes/BQueryBoundingBox.png)

b. Informar sobre el estado de la ingesta de datos sin utilizar una solución de polling

Cloud Functions tiene la capacidad de entregar información sobre el proceso de ingesta de los datos a través de sus paneles con métricas y logging. 

![Monitoring y logging](https://github.com/sebakjal/NW_challenge/blob/main/imagenes/CloudFunctionsMonitoring.png)

3. La solución debe ser escalable a 100 millones de entradas. Se recomienda simplificar los datos mediante un modelo de datos. Agregue pruebas de que la solución es escalable.

Para simplificar los datos estos se separan en tablas regionales, se facilitan las queries agrupando con un sistema de grilla intuitivo y se particionan los datos por la hora del viaje. Opcionalmente se pueden agregar las columnas con distancias en metros si así se quisiera, que son más manejables que las coordenadas geográficas. Estas están generadas en el código pero no agregadas en la tabla final por simplicidad.

Para probar la escalabilidad de esta tabla se realizaron pruebas agregando una gran cantidad de registros y comprobando que el tiempo de procesamiento no escala linealmente. En un principio se prueba haciendo una consulta a todos los registros originales de la tabla de Praga:

![34rows](https://github.com/sebakjal/NW_challenge/blob/main/imagenes/34rows.png)

En esta se puede ver que la query demoró 487 ms, medio segundo. Teniendo esta query como parámetro se comienzan a agregar más entradas a las tablas y se prueba la misma query, para ver como sube el tiempo de consulta. Se hicieron pruebas con 170, 7786 y 95293 registros:

![170rows](https://github.com/sebakjal/NW_challenge/blob/main/imagenes/170rows.jpeg)

![7786rows](https://github.com/sebakjal/NW_challenge/blob/main/imagenes/7786rows.png)

![95293rows](https://github.com/sebakjal/NW_challenge/blob/main/imagenes/95293rows.jpeg)

A partir de estas pruebas se puede constatar que a pesar de que la cantidad de registros ha crecido en más de mil veces, la respuesta sigue demorando menos de 2 segundos.

4. La solución debe estar escrita en Python usando una base de datos SQL

Tanto la solución principal de limpieza de datos como la función de ingesta en Cloud Functions están escritas en Python y se pueden revisar en este repositorio. BigQuery en tanto usa lenguaje SQL para trabajar.

5. Puntos de bonificación si incluye su solución en contenedores y si dibuja cómo configuraría la aplicación en GCP

La solución no se ha alcanzado a llevar a contenedores. Por otro lado, la solución ya está hecha sobre GCP. Sin embargo, hay que hacer algunas modificaciones para usarla en otro proyecto. Con esto se refiere a cambiar los nombres de los datasets de BigQuery, buckets de Cloud Storage y setear los permisos necesarios para escritura y lectura a los usuarios del proyecto.


# Código del script local para limpiar los datos desde archivos .csv

Este es el script principal que sirve para hacer la limpieza y formateo de datos desde los archivos .csv. Este archivo tiene que estar en una carpeta local junto con los .csv que se quieran procesar (y que estén en el formato entregado con el enunciado). Se recomienda leer documentación en GitHub antes.

En el siguiente bloque se importan las librerías necesarias para el código:
- pandas se usa para ordenar los datos en tablas
- glob se usa para acceder los archivos dentro de la carpeta local
- os se usa para usar varias funciones de modificación de archivos
- pyproj se usa para realizar transformaciones geoespaciales

```
import pandas as pd
import glob
import os
from pyproj import Transformer
```

En el siguiente bloque se setean variables auxiliares:

```
original_dir = "original"
upload_dir = "upload"
daily_dataframes = []
```
En el siguiente bloque se crean sub carpetas con las que se trabaja en el script. La carpeta "original" se usa para guardar los .csv originales que ya fueron procesados y "upload" para dejar los .csv listos para subir a la nube:

```
try:
    if os.path.isdir(original_dir):
        pass
    else:
        os.mkdir(original_dir)

    if os.path.isdir(upload_dir):
        pass
    else:
        os.mkdir(upload_dir)
except:
    print('Problema con la creación de directorios')
```

En el siguiente bloque se encuentra la lógica principal del script. Dentro del primer ciclo se revisan todos los archivos .csv dentro de la carpeta, se verifica el formato de estos archivos, se crea un dataframe por cada archivo de entrada y se inicializan variables auxiliares importantes. Estas variable importantes son:

- Diccionario con el código EPSG de la zona de la región junto a la ubicación del punto de origen de la grilla propuesta
- Diccionario con los valores que se usarán en el eje Y para transformar luego a strings

Una de las desventajas de esta solución temporalmente es la de tener que modificar estos diccionarios manualmente cuando se agreguen nuevas regiones y/o las strings no den a basto para el tamaño de la grilla.

Dentro del segundo ciclo se encuentran el proceso de limpieza y formateo de datos en sí. Para cada ciudad en los archivos .csv se pasa por este ciclo y se crea un dataframe.

```
# Se revisan todos los archivos .csv de la carpeta
for csv_file in glob.glob('*.csv'):

    # Para cada archivo:

    # Se lee el archivo .csv
    with open(csv_file, 'r') as f:
        trips = f.read()

        # Se verifica que los headers sean los correspondientes al formato
        first_line = trips.split('\n', 1)[0]
        if first_line != 'region,origin_coord,destination_coord,datetime,datasource':
            raise Exception('El archivo ' + csv_file + ' no está en el formato adecuado')

    # Se reemplazan algunos carácteres innecesarios del archivo
    replacements = [('POINT (', ''),
                    (')', ''),
                    (' ', ',')]
    for find, replacement in replacements:
        trips = trips.replace(find, replacement)

    # Se copia el texto limpio a un nuevo archivo con prefijo 'new_'
    new_trips_path = 'new_' + csv_file
    with open(new_trips_path, 'w') as f:
        f.write(trips)

    # Se inicializan variables auxiliares para la grilla
    cities = {'Turin': {'epsg': 32632, 'x0': 381000, 'y0': 4980000},
              'Hamburg': {'epsg': 32632, 'x0': 551000, 'y0': 5918000},
              'Prague': {'epsg': 32633, 'x0': 450000, 'y0': 5536000}}
    alphabet = {'1': 'a', '2': 'b', '3': 'c', '4': 'd', '5': 'e', '6': 'f', '7': 'g', '8': 'h', '9': 'i', '10': 'j',
                '11': 'k', '12': 'l', '13': 'm', '14': 'n', '15': 'o', '16': 'p', '17': 'q', '18': 'r', '19': 's',
                '20': 't', '21': 'u', '22': 'v', '23': 'w', '24': 'x', '25': 'y', '26': 'z', '27': 'aa', '28': 'ab',
                '29': 'ac', '30': 'ad', '31': 'ae', '32': 'af'}
    df_list = []

    # Se crea un dataframe de pandas con los datos del archivo
    new_trips_df = pd.read_csv(new_trips_path, header=0, names=['region', 'origin_x', 'origin_y', 'destination_x',
                                                                'destination_y', 'date', 'timestamp', 'datasource'])
    # Por cada ciudad en la lista "cities":
    for city in cities.keys():

        # Se crea un dataframe con las filas que coinciden con el nombre de la ciudad
        df = pd.DataFrame(new_trips_df[new_trips_df['region'] == city])

        # Se crean columnas con el tiempo en formato yyyy-mm-dd hh:mm:ss y además otra solo con la hora
        df['hora'] = df['timestamp'].str.split(':', 1).str[0]
        df['timestamp'] = df['date'] + ' ' + df['timestamp'] + ':00'
        df['timestamp'] = pd.to_datetime(df.timestamp)

        # Se crea un objeto Transformer, que permite transformar las coordenadas geográficas (Código EPSG: 4326) a
        # coordenadas proyectadas. Esta transformación depende de la zona del mundo, por esto se necesita el código
        # EPSG específico. Esta transformación se hace dado que las coordenadas proyectadas son más intuitivas de usar.
        transformer = Transformer.from_crs(4326, cities[city]['epsg'], always_xy=True)

        # Se transforman las coordenadas de ORIGEN y se asignan a columnas
        xx, yy = transformer.transform(df['origin_x'].values, df['origin_y'].values)
        df['easting_origin'] = xx
        df['northing_origin'] = yy

        # Se asignan valores enteros a las celdas de origen de la grilla. Para el eje Y estas se transforman a letras
        df['origin_cell_x'] = (df['easting_origin'] - cities[city]['x0']) / 1000 + 1
        df['origin_cell_x'] = df['origin_cell_x'].astype(int).astype(str)
        df['origin_cell_y'] = (df['northing_origin'] - cities[city]['y0']) / 1000 + 1
        df['origin_cell_y'] = df['origin_cell_y'].astype(int).astype(str)
        df.replace({'origin_cell_y': alphabet}, inplace=True)

        # El valor de la celda de origen corresponde a una string compuesta por el valor del entero de X y de la string
        # en Y
        df['origin_cell'] = df['origin_cell_x'] + df['origin_cell_y']

        # Se transforman las coordenadas de DESTINO y se asignan a columnas
        xx, yy = transformer.transform(df['destination_x'].values, df['destination_y'].values)
        df['easting_destination'] = xx
        df['northing_destination'] = yy

        # Se asignan valores enteros a las celdas de destino de la grilla. Para el eje Y estas se transforman a letras
        df['destination_cell_x'] = (df['easting_destination'] - cities[city]['x0']) / 1000 + 1
        df['destination_cell_x'] = df['destination_cell_x'].astype(int).astype(str)
        df['destination_cell_y'] = (df['northing_destination'] - cities[city]['y0']) / 1000 + 1
        df['destination_cell_y'] = df['destination_cell_y'].astype(int).astype(str)
        df.replace({'destination_cell_y': alphabet}, inplace=True)

        # El valor de la celda de destino corresponde a una string compuesta por el valor del entero de X y de la string
        # en Y
        df['destination_cell'] = df['destination_cell_x'] + df['destination_cell_y']

        # El dataframe resultante de la ciudad se agrega a una lista
        df_list.append(df)

    # Se concatena la lista de dataframes para dejar uno condensado con todas las ciudades
    df_cities = pd.concat(df_list)

    # Se agrega a la lista daily_dataframes el dataframe df_cities, que corresponde al dataframe creado desde UN .csv
    # Se toman las columnas con información significativa
    daily_dataframes.append(df_cities[['region', 'timestamp', 'hora', 'origin_cell', 'destination_cell', 'origin_x',
                                       'origin_y', 'destination_x', 'destination_y', 'datasource']])

    # Se elimina el archivo .csv temporal limpio creado al principio del ciclo. El original se mueve a una sub carpeta
    try:
        os.remove(new_trips_path)
        os.rename(csv_file, original_dir + '/' + csv_file)
    except:
        print('Error en el movimiento del archivos')
```
En este último bloque se crea el dataframe con todos los datos del día y se crea un .csv con esta información, que luego se mueve a una sub carpeta.

```
# Se concatenan los dataframes de todos los archivos del día y se transforman en un .csv. Este archivo se mueve a una
# sub carpeta para cargarlo posteriormente.
if not daily_dataframes:
    print('No hay dataframes')
else:
    df_upload = pd.concat(daily_dataframes)
    df_upload.to_csv(upload_dir + '/formatted_trips.csv', index=False)
```


# Código de la función usada en Cloud Functions (FaaS)

Esta esta función tiene un trigger que se activa cuando un nuevo archivo se carga dentro de cierto bucket en Cloud Storage, y lo que hace es tomar este archivo (.csv) ya limpio que fue subido en el bucket y carga su contenido a las tablas correspondientes en el dataset de BigQuery.

```
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

        dataframe = cities_df[cities_df['region'] == city ]
        table_id = '{}.{}.{}'.format(project, dataset, city.lower())

        load_job = client.load_table_from_dataframe(
            dataframe, table_id, job_config=job_config
        )

        load_job.result()
        print("Loaded {} rows into the {} table.".format(str(load_job.output_rows), city.lower()))
    
    return 'Check the results in the logs'
```

Hay que tener en cuenta ciertos requerimientos para poder usar esta función correctamente en Cloud Functions:

- Se deben cambiar los nombres de las variables del bucket, project y dataset a los valores del proyecto propio 
- Se debe tener permiso para escritura en BigQuery
- Se debe cuidar que la función esté alojada en la misma región que el dataset de Bigquery al que se quiere cargar datos
- Se debe cargar en el mismo espacio que la función un archivo "requeriments.txt" donde se escriban los requerimientos de la función (mostrados en la siguiente celda)

### requeriments.txt

```
google-cloud-bigquery==3.4.0
gcsfs
pandas
fsspec
```

# Código del DAG de Airflow para hacer la limpieza de datos y subida del archivo a Cloud Storage

Este código lo que hace es realizar 3 tareas diariamente:

- Corre el notebook con el código para limpiar los datos de los archivos .csv (csv_process.ipynb)
- Espera 5 minutos para asegurarse que la limpieza ha terminado correctamente
- Sube los archivos creados por el notebook a un bucket de Cloud Storage}

```
import datetime
import os
import pendulum
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.providers.papermill.operators.papermill import PapermillOperator


# Seteo de variables
home_path = os.path.expanduser('~')

# Reemplazar con la carpeta donde se ubican el notebook csv_process.ipynb y los .csv
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

    # Para el video el comando se cambia a 10 segundos temporalmente
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
```
    
Este archivo (nw_DAG.py) debe integrarse en la carpeta de DAGs de Airflow.
Adicionalmente deben correrse los siguiente comandas para instalar y actualizar dependencias:

- pip install papermill
- pip install apache-airflow-providers-papermill
- pip install --upgrade pip ipython ipykernel
- ipython kernel install --name "Python3" --user
