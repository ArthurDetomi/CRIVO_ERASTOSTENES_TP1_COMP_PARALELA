import csv
import subprocess
import re
import os
import matplotlib.pyplot as plt

def ler_parametros_csv(caminho_arquivo):
    """Lê o CSV e retorna listas ordenadas de Entradas e Número de Processos."""
    entradas = set()
    processos = set()
    
    with open(caminho_arquivo, mode='r', encoding='utf-8') as arquivo:
        leitor = csv.DictReader(arquivo)
        for linha in leitor:
            if linha.get('Entradas') and linha['Entradas'].strip():
                entradas.add(int(linha['Entradas'].strip()))
            if linha.get('N processos') and linha['N processos'].strip():
                processos.add(int(linha['N processos'].strip()))
                
    return sorted(list(entradas)), sorted(list(processos))

def compilar_projeto(diretorio):
    """Executa o comando 'make' no diretório especificado."""
    print(f"[{diretorio}] Compilando projeto...")
    resultado = subprocess.run(['make'], cwd=diretorio, capture_output=True, text=True)
    if resultado.returncode != 0:
        print(f"Erro ao compilar em {diretorio}:\n{resultado.stderr}")
        exit(1)

def executar_e_capturar(comando, diretorio, regex_tempo):
    """Executa um comando no SO e extrai o tempo da saída usando Regex."""
    resultado = subprocess.run(comando, cwd=diretorio, capture_output=True, text=True)
    
    if resultado.returncode != 0:
        print(f"Erro ao executar {' '.join(comando)}:\n{resultado.stderr}")
        return None
        
    match = re.search(regex_tempo, resultado.stdout)
    if match:
        return float(match.group(1))
    else:
        print(f"Aviso: Não foi possível capturar o tempo na saída: {resultado.stdout}")
        return None

def plotar_graficos(entradas, processos, dados):
    """Gera gráficos de Tempo, Speedup e Eficiência."""
    
    # Criando uma figura com 3 subplots
    fig, axs = plt.subplots(1, 3, figsize=(18, 5))
    
    for n in entradas:
        tempos_paralelos = [dados[n]['paralelo'][p] for p in processos]
        tempo_linear = dados[n]['linear']
        
        # 1. Gráfico de Tempo de Execução
        axs[0].plot(processos, tempos_paralelos, marker='o', label=f'N={n}')
        axs[0].axhline(y=tempo_linear, linestyle='--', color='gray', alpha=0.5)
        
        # 2. Gráfico de Speedup
        speedups = [tempo_linear / tp if tp > 0 else 0 for tp in tempos_paralelos]
        axs[1].plot(processos, speedups, marker='o', label=f'N={n}')
        
        # 3. Gráfico de Eficiência
        eficiencias = [s / p for s, p in zip(speedups, processos)]
        axs[2].plot(processos, eficiencias, marker='o', label=f'N={n}')

    # Configurações do Gráfico de Tempo
    axs[0].set_title("Tempo de Execução vs Processos")
    axs[0].set_xlabel("Número de Processos (MPI)")
    axs[0].set_ylabel("Tempo (segundos)")
    axs[0].legend()
    axs[0].grid(True)

    # Configurações do Gráfico de Speedup
    axs[1].set_title("Speedup vs Processos")
    axs[1].set_xlabel("Número de Processos (MPI)")
    axs[1].set_ylabel("Speedup")
    # Linha de Speedup ideal (S = P)
    axs[1].plot(processos, processos, 'k--', label='Speedup Ideal')
    axs[1].legend()
    axs[1].grid(True)

    # Configurações do Gráfico de Eficiência
    axs[2].set_title("Eficiência vs Processos")
    axs[2].set_xlabel("Número de Processos (MPI)")
    axs[2].set_ylabel("Eficiência")
    # Linha de Eficiência ideal (E = 1)
    axs[2].axhline(y=1.0, color='k', linestyle='--', label='Eficiência Ideal')
    axs[2].legend()
    axs[2].grid(True)

    plt.tight_layout()
    plt.savefig('relatorio_desempenho.png')
    print("\n[+] Gráficos gerados com sucesso e salvos em 'relatorio_desempenho.png'!")
    plt.show()

def main():
    arquivo_csv = 'testes.csv'
    
    if not os.path.exists(arquivo_csv):
        print(f"Arquivo {arquivo_csv} não encontrado.")
        return
        
    entradas, processos = ler_parametros_csv(arquivo_csv)
    print(f"Valores de N encontrados: {entradas}")
    print(f"Valores de Processos MPI encontrados: {processos}")
    
    compilar_projeto('./linear')
    compilar_projeto('./paralelo')
    
    dados = {}
    
    for n in entradas:
        dados[n] = {'linear': 0.0, 'paralelo': {}}
        
        # Executa a versão Linear
        print(f"\n--- Executando testes para N = {n} ---")
        print(f"Rodando versão Linear...")
        t_linear = executar_e_capturar(
            comando=['./crivo_linear', str(n)], 
            diretorio='./linear', 
            regex_tempo=r'Tempo Real:\s*([0-9]+\.[0-9]+)'
        )
        
        if t_linear is not None:
            dados[n]['linear'] = t_linear
        
        # Executa a versão Paralela para cada N processos
        for p in processos:
            print(f"Rodando versão Paralela com {p} processos...")
            t_paralelo = executar_e_capturar(
                comando=['mpirun', '-n', str(p), './crivo_paralelo', str(n)],
                diretorio='./paralelo',
                regex_tempo=r'Tempo paralelo:\s*([0-9]+\.[0-9]+)'
            )
            
            if t_paralelo is not None:
                dados[n]['paralelo'][p] = t_paralelo
                
    plotar_graficos(entradas, processos, dados)

if __name__ == '__main__':
    main()