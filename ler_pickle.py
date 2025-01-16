import pickle
import os

def ler_bot_data(nome_arquivo="bot_data.pickle"):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    persistence_file = os.path.join(script_dir, nome_arquivo)

    try:
        with open(persistence_file, 'rb') as f:
            data = pickle.load(f)
            print(data)  # Imprime o conteúdo do bot_data
    except FileNotFoundError:
        print(f"Arquivo não encontrado: {persistence_file}")
    except Exception as e:
        print(f"Erro ao ler o arquivo: {e}")

if __name__ == "__main__":
    ler_bot_data()  # Ou ler_bot_data("nome_do_seu_arquivo.pickle") se necessário