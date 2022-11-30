# Challenge de Neuralworks

El challenge consiste en crear un proyecto de ingesta de datos que toma los datos desde un .csv, los agrupe según ciertas características y los suba a una base de datos para que luego puedan ser utilizados para análisis posteriores. En estos primeros párrafos se explica como se realiza la solución, mientras que en los últimos se responden las preguntas en específico.

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

AGREGAR PRUEBAS DE ESCALABILIDAD


4. La solución debe estar escrita en Python usando una base de datos SQL

Tanto la solución principal de limpieza de datos como la función de ingesta en Cloud Functions están escritas en Python y se pueden revisar en este repositorio. BigQuery en tanto usa lenguaje SQL para trabajar.

5. Puntos de bonificación si incluye su solución en contenedores y si dibuja cómo configuraría la aplicación en GCP

La solución no se ha alcanzado a llevar a contenedores. Por otro lado, la solución ya está hecha sobre GCP. Sin embargo, hay que hacer algunas modificaciones para usarla en otro proyecto. Con esto se refiere a cambiar los nombres de los datasets de BigQuery, buckets de Cloud Storage y setear los permisos necesarios para escritura y lectura a los usuarios del proyecto.

