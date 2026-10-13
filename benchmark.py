import csv
import re
import statistics
import subprocess
from pathlib import Path

import matplotlib.pyplot as plt


# ============================================================
# CONFIGURAÇÕES
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DIRETORIO_LINEAR = BASE_DIR / "linear"
DIRETORIO_PARALELO = BASE_DIR / "paralelo"
ARQUIVO_TESTES = BASE_DIR / "testes.csv"

# Quantidade de execuções da versão paralela por configuração.
# A versão linear executa apenas uma vez por valor de N.
REPETICOES_PARALELO = 5

# Expressões regulares para extrair os tempos impressos pelos C.
PADRAO_LINEAR = (
    r"Tempo Real:\s*([-+]?\d+(?:\.\d*)?(?:[eE][-+]?\d+)?)\s*segundos"
)

PADRAO_PARALELO = (
    r"Tempo paralelo:\s*([-+]?\d+(?:\.\d*)?(?:[eE][-+]?\d+)?)\s*segundos"
)


# ============================================================
# COMPILAÇÃO
# ============================================================

def compilar_programas():
    """Compila as versões linear e paralela."""

    print("Compilando versão linear...")

    subprocess.run(
        ["make"],
        cwd=DIRETORIO_LINEAR,
        check=True
    )

    print("Compilando versão paralela...")

    subprocess.run(
        ["make"],
        cwd=DIRETORIO_PARALELO,
        check=True
    )

    print("Compilação concluída.\n")


# ============================================================
# EXECUÇÃO E EXTRAÇÃO DOS TEMPOS
# ============================================================

def executar_e_obter_tempo(comando, diretorio, padrao):
    """
    Executa um programa e extrai o tempo que ele próprio imprime.

    Não utiliza time.perf_counter() nem mede externamente
    a duração do processo.
    """

    resultado = subprocess.run(
        comando,
        cwd=diretorio,
        capture_output=True,
        text=True
    )

    saida = resultado.stdout + "\n" + resultado.stderr

    if resultado.returncode != 0:
        raise RuntimeError(
            f"Erro ao executar: {' '.join(comando)}\n"
            f"Código de saída: {resultado.returncode}\n"
            f"Saída do programa:\n{saida}"
        )

    correspondencia = re.search(padrao, saida)

    if correspondencia is None:
        raise ValueError(
            f"Não foi possível encontrar o tempo na saída.\n"
            f"Comando: {' '.join(comando)}\n"
            f"Saída recebida:\n{saida}"
        )

    return float(correspondencia.group(1))


def executar_linear(n):
    """Executa a versão linear uma vez para o valor informado de N."""

    return executar_e_obter_tempo(
        ["./crivo_linear", str(n)],
        DIRETORIO_LINEAR,
        PADRAO_LINEAR
    )


def executar_paralelo(n, processos):
    """Executa a versão MPI para N e a quantidade de processos informada."""

    comando = [
        "mpirun",
        "-n", str(processos),
        "./crivo_paralelo",
        str(n)
    ]

    return executar_e_obter_tempo(
        comando,
        DIRETORIO_PARALELO,
        PADRAO_PARALELO
    )


# ============================================================
# LEITURA DO CSV
# ============================================================

def carregar_testes():
    """
    Lê testes.csv, com as colunas:

    Entradas,N processos

    Se Entradas estiver vazia, reutiliza o último N informado.
    """

    testes = []
    ultimo_n = None

    with open(
        ARQUIVO_TESTES,
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as arquivo:

        leitor = csv.DictReader(arquivo)

        colunas = leitor.fieldnames or []

        if "Entradas" not in colunas or "N processos" not in colunas:
            raise ValueError(
                "O CSV precisa conter as colunas "
                "'Entradas' e 'N processos'."
            )

        for numero_linha, linha in enumerate(leitor, start=2):
            valor_n = (linha.get("Entradas") or "").strip()
            valor_processos = (linha.get("N processos") or "").strip()

            if valor_n:
                n = int(valor_n)
                ultimo_n = n

            elif ultimo_n is not None:
                n = ultimo_n

            else:
                raise ValueError(
                    f"Linha {numero_linha}: o primeiro valor de N "
                    "não pode estar vazio."
                )

            if not valor_processos:
                raise ValueError(
                    f"Linha {numero_linha}: quantidade de processos vazia."
                )

            processos = int(valor_processos)

            if n < 2:
                raise ValueError(
                    f"Linha {numero_linha}: N deve ser maior ou igual a 2."
                )

            if processos < 1:
                raise ValueError(
                    f"Linha {numero_linha}: a quantidade de processos "
                    "deve ser positiva."
                )

            testes.append({
                "n": n,
                "processos": processos
            })

    if not testes:
        raise ValueError("Nenhum teste foi encontrado no CSV.")

    return testes


# ============================================================
# EXECUÇÃO DOS TESTES
# ============================================================

def realizar_testes(testes):
    """
    Executa cada teste.

    A versão linear é executada uma única vez para cada N distinto.
    A versão paralela é executada várias vezes para cada combinação
    de N e quantidade de processos.
    """

    resultados = []

    # Guarda o tempo linear de cada N para não executar
    # novamente a versão linear quando P mudar.
    tempos_lineares = {}

    for teste in testes:
        n = teste["n"]
        processos = teste["processos"]

        print("\n" + "=" * 60)
        print(f"Entradas (N): {n}")
        print(f"Processos MPI: {processos}")
        print("=" * 60)

        # ----------------------------------------------------
        # Versão linear: uma única execução por valor de N
        # ----------------------------------------------------

        if n not in tempos_lineares:
            print("\nExecutando versão linear pela primeira vez para este N...")

            tempo_linear = executar_linear(n)

            if tempo_linear <= 0:
                raise ValueError(
                    f"O tempo linear para N={n} foi "
                    f"{tempo_linear:.8f} s. "
                    "Não é possível calcular o speedup com esse valor."
                )

            tempos_lineares[n] = tempo_linear

            print(f"Tempo linear: {tempo_linear:.8f} segundos")

        else:
            tempo_linear = tempos_lineares[n]

            print("\nReutilizando o tempo linear já calculado.")
            print(f"Tempo linear: {tempo_linear:.8f} segundos")

        # ----------------------------------------------------
        # Versão paralela: múltiplas execuções
        # ----------------------------------------------------

        tempos_paralelos = []

        for repeticao in range(1, REPETICOES_PARALELO + 1):
            print(
                f"\nExecução paralela "
                f"{repeticao}/{REPETICOES_PARALELO}..."
            )

            tempo = executar_paralelo(n, processos)
            tempos_paralelos.append(tempo)

            print(f"Tempo paralelo: {tempo:.8f} segundos")

        # Mediana das execuções paralelas
        tempo_paralelo = statistics.median(tempos_paralelos)

        if tempo_paralelo <= 0:
            raise ValueError(
                f"O tempo paralelo para N={n} e P={processos} "
                f"foi {tempo_paralelo:.8f} s. "
                "Verifique se o programa C está imprimindo o tempo "
                "com precisão suficiente."
            )

        print("\n--- Resultado da configuração ---")
        print(f"Mediana paralela: {tempo_paralelo:.8f} segundos")

        # ----------------------------------------------------
        # Speedup e eficiência
        # ----------------------------------------------------

        speedup = tempo_linear / tempo_paralelo
        eficiencia = (speedup / processos) * 100

        print(f"Speedup: {speedup:.8f}")
        print(f"Eficiência: {eficiencia:.8f}%")

        resultados.append({
            "Entradas": n,
            "N processos": processos,
            "Tempo linear (s)": tempo_linear,
            "Tempo paralelo (s)": tempo_paralelo,
            "Speedup": speedup,
            "Eficiência (%)": eficiencia
        })

    return resultados


# ============================================================
# SALVAMENTO DOS RESULTADOS
# ============================================================

def salvar_csv(resultados):
    """Salva os resultados em resultados.csv com oito casas decimais."""

    arquivo_saida = BASE_DIR / "resultados.csv"

    colunas = [
        "Entradas",
        "N processos",
        "Tempo linear (s)",
        "Tempo paralelo (s)",
        "Speedup",
        "Eficiência (%)"
    ]

    with open(
        arquivo_saida,
        "w",
        encoding="utf-8",
        newline=""
    ) as arquivo:

        escritor = csv.DictWriter(arquivo, fieldnames=colunas)
        escritor.writeheader()

        for resultado in resultados:
            escritor.writerow({
                "Entradas": resultado["Entradas"],
                "N processos": resultado["N processos"],
                "Tempo linear (s)": (
                    f"{resultado['Tempo linear (s)']:.8f}"
                ),
                "Tempo paralelo (s)": (
                    f"{resultado['Tempo paralelo (s)']:.8f}"
                ),
                "Speedup": f"{resultado['Speedup']:.8f}",
                "Eficiência (%)": (
                    f"{resultado['Eficiência (%)']:.8f}"
                )
            })

    print(f"\nResultados salvos em: {arquivo_saida}")


# ============================================================
# GERAÇÃO DOS GRÁFICOS
# ============================================================

def gerar_graficos(resultados):
    """Gera gráficos para comparar os tempos e o desempenho paralelo."""

    rotulos = [
        f"N={r['Entradas']:,}\nP={r['N processos']}"
        for r in resultados
    ]

    tempos_lineares = [
        r["Tempo linear (s)"] for r in resultados
    ]

    tempos_paralelos = [
        r["Tempo paralelo (s)"] for r in resultados
    ]

    speedups = [
        r["Speedup"] for r in resultados
    ]

    eficiencias = [
        r["Eficiência (%)"] for r in resultados
    ]

    posicoes = list(range(len(resultados)))
    largura = 0.38

    # --------------------------------------------------------
    # Gráfico 1: comparação de tempos
    # --------------------------------------------------------

    plt.figure(figsize=(12, 6))

    plt.bar(
        [p - largura / 2 for p in posicoes],
        tempos_lineares,
        largura,
        label="Linear"
    )

    plt.bar(
        [p + largura / 2 for p in posicoes],
        tempos_paralelos,
        largura,
        label="Paralelo"
    )

    plt.xticks(posicoes, rotulos)
    plt.yscale("log")
    plt.xlabel("Entrada e quantidade de processos")
    plt.ylabel("Tempo (segundos)")
    plt.title("Comparação dos tempos de execução")
    plt.legend()
    plt.grid(axis="y", alpha=0.3)
    plt.tight_layout()

    plt.savefig(
        BASE_DIR / "comparacao_tempos.png",
        dpi=150
    )

    plt.close()

    # --------------------------------------------------------
    # Gráfico 2: speedup
    # --------------------------------------------------------

    plt.figure(figsize=(12, 6))

    plt.bar(posicoes, speedups)

    plt.axhline(
        y=1,
        linestyle="--",
        label="Speedup = 1"
    )

    plt.xticks(posicoes, rotulos)
    plt.xlabel("Entrada e quantidade de processos")
    plt.ylabel("Speedup")
    plt.title("Speedup da versão paralela")
    plt.legend()
    plt.grid(axis="y", alpha=0.3)
    plt.tight_layout()

    plt.savefig(
        BASE_DIR / "speedup.png",
        dpi=150
    )

    plt.close()

    # --------------------------------------------------------
    # Gráfico 3: eficiência
    # --------------------------------------------------------

    plt.figure(figsize=(12, 6))

    plt.bar(posicoes, eficiencias)

    plt.axhline(
        y=100,
        linestyle="--",
        label="Eficiência = 100%"
    )

    plt.xticks(posicoes, rotulos)
    plt.xlabel("Entrada e quantidade de processos")
    plt.ylabel("Eficiência (%)")
    plt.title("Eficiência paralela")
    plt.legend()
    plt.grid(axis="y", alpha=0.3)
    plt.tight_layout()

    plt.savefig(
        BASE_DIR / "eficiencia.png",
        dpi=150
    )

    plt.close()

    print("\nGráficos gerados:")
    print("  comparacao_tempos.png")
    print("  speedup.png")
    print("  eficiencia.png")


# ============================================================
# FUNÇÃO PRINCIPAL
# ============================================================

def main():
    try:
        testes = carregar_testes()

        print(f"Configurações de teste: {len(testes)}")
        print(f"Repetições paralelas por configuração: {REPETICOES_PARALELO}")

        compilar_programas()

        resultados = realizar_testes(testes)

        salvar_csv(resultados)
        gerar_graficos(resultados)

        print("\nTodos os testes foram concluídos!")

    except (
        ValueError,
        OSError,
        RuntimeError,
        subprocess.CalledProcessError
    ) as erro:
        print(f"\nErro: {erro}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()