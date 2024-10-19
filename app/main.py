from fastapi import FastAPI, Depends, BackgroundTasks
from .controllers.sensor_controller import router as sensor_router  # Telling which name this route will had
from .db import connection, get_garden_db, get_garden_complete_db
import asyncio
import pandas as pd

#  FastAPI Description
app = FastAPI()


# Routes
app.include_router(sensor_router)  # Sensor Route


# ------------ App Events
# Startup
@app.on_event("startup")
async def startup_event():
    connection()        # Database connection
    asyncio.create_task(monitor_garden_db())    # Monitoring the garden database
    
    
    
# Function to monitor garden database
async def monitor_garden_db():    
    try:
        while True:
            await asyncio.sleep(30)  # 10800 seconds = 3 hours ## Wait 3 hours to check database
            
            garden_db = get_garden_db()    
            sensor_data = await garden_db.sensor_data.find().to_list(length=None)
            
            if len(sensor_data) >= 4:
                result = await generate_correlation_matrix(sensor_data)
                print(result["status"])
    except Exception as e:
        print(e)
    
# Function to create correlation matrix and send to database complete
async def generate_correlation_matrix(sensor_data):
    try:
        # Verificando se o sensor_data não é None e é uma lista ou DataFrame
        if sensor_data is None or not isinstance(sensor_data, (list, pd.DataFrame)):
            raise ValueError("sensor_data deve ser uma lista ou um DataFrame")

        # Imprimindo os dados recebidos para verificação
        print("Dados recebidos:", sensor_data)

        # Convertendo os dados em um DataFrame do pandas
        df = pd.DataFrame(sensor_data)

        # Verificando a estrutura do DataFrame
        print("DataFrame inicial:\n", df)

        # Verificando se a coluna 'measurements' existe
        if 'data' not in df.columns:
            raise ValueError("A coluna 'measurements' não foi encontrada nos dados")

        # Expandindo a coluna 'measurements' para normalizar os dados
        expanded_data = df.explode('data')
        print("Data após explode:\n", expanded_data)

        # Normalizando a coluna 'measurements'
        measurements_df = pd.json_normalize(expanded_data['data'])

        # Verificando se o measurements_df não está vazio
        if measurements_df.empty:
            raise ValueError("O DataFrame de medições está vazio")

        print("DataFrame de medições:\n", measurements_df)

        # Combinando os dados expandidos com os timestamps
        combined_df = pd.concat([expanded_data[['timestamp']], measurements_df], axis=1)

        # Verificando a estrutura do combined_df
        print("DataFrame combinado:\n", combined_df)

        # Filtrando apenas as linhas onde 'measure_value' é numérico
        combined_df['measure_value'] = pd.to_numeric(combined_df['measure_value'], errors='coerce')

        # Removendo linhas com NaN em 'measure_value'
        combined_df = combined_df.dropna(subset=['measure_value'])

        # Resetando o índice para garantir que ele seja único
        combined_df.reset_index(drop=True, inplace=True)

        # Garantindo que o índice seja único antes de calcular a matriz de correlação
        if not combined_df.index.is_unique:
            combined_df = combined_df.loc[~combined_df.index.duplicated(keep='first')]

        # Usando a média para calcular a matriz de correlação
        correlation_matrix = combined_df.groupby('timestamp').mean().corr()

        # Verificando a matriz de correlação
        print("Matriz de correlação:\n", correlation_matrix)

        # Armazenando a matriz de correlação no banco garden_complete
        garden_complete_db = await get_garden_complete_db()
        correlation_result = {
            "correlation_matrix": correlation_matrix.to_dict(),
            "timestamp": pd.Timestamp.now().isoformat()
        }

        await garden_complete_db.correlation_data.insert_one(correlation_result)

        return {"status": "Matriz de correlação gerada e salva com sucesso."}

    except ValueError as ve:
        print(f"Valor de erro: {ve}")
        return {"status": "Erro", "message": str(ve)}

    except Exception as e:
        print(f"Ocorreu um erro: {e}")
        return {"status": "Erro", "message": str(e)}