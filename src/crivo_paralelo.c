#include <mpi/mpi.h>

#include <stdlib.h>

#include <stdio.h>

#include <math.h>

#define TAG1 10
#define TAG2 20

void crivo_paralelo(char *primos_local, char *primos_base, int inicio, int fim,
                    int limite) {

  for (int p = 2; p <= limite; p++) {
    if (primos_base[p]) {

      int primeiro_multiplo = p * p;

      if (primeiro_multiplo < inicio) {
        primeiro_multiplo = ((inicio + p - 1) / p) * p;
      }

      for (int multiplo = primeiro_multiplo; multiplo <= fim; multiplo += p) {

        primos_local[multiplo - inicio] = 0;
      }
    }
  }
}

void liberar_memoria(void **array) {
  free(*array);
  *array = NULL;
}

int main(int argc, char **argv) {
  MPI_Init(&argc, &argv);

  int n = 100000000;
  int size, rank;

  MPI_Comm_rank(MPI_COMM_WORLD, &rank);
  MPI_Comm_size(MPI_COMM_WORLD, &size);

  int quantidade = n - 1;
  int tamanho_base = quantidade / size;
  int resto = quantidade % size;

  int tamanho_local = tamanho_base;

  if (rank < resto) {
    tamanho_local++;
  }

  // Até [2, N]
  int inicio = 2 + (rank * tamanho_base);
  if (rank < resto) {
    inicio += rank;
  } else {
    inicio += resto;
  }

  int fim = inicio + tamanho_local - 1;

  printf("Rank %d: Responsavel pelo intervalo [%d, %d]\n", rank, inicio, fim);

  char *primos_local = (char *)malloc(tamanho_local);

  for (int i = 0; i < tamanho_local; i++) {
    primos_local[i] = 1;
  }

  int limite = sqrt(n);

  char *primos_base = malloc(limite + 1);

  if (rank == 0) {
    for (int i = 0; i <= limite; i++) {
      primos_base[i] = 1;
    }

    primos_base[0] = primos_base[1] = 0;

    for (int p = 2; p * p <= limite; p++) {
      if (primos_base[p]) {
        for (int multiplo = p * p; multiplo <= limite; multiplo += p) {
          primos_base[multiplo] = 0;
        }
      }
    }
  }

  MPI_Bcast(primos_base, limite + 1, MPI_CHAR, 0, MPI_COMM_WORLD);

  crivo_paralelo(primos_local, primos_base, inicio, fim, limite);
  char *primos_final = NULL;

  if (rank == 0) {
    primos_final = malloc(quantidade);
  }

  MPI_Gather(primos_local, tamanho_local, MPI_CHAR, primos_final, tamanho_local,
             MPI_CHAR, 0, MPI_COMM_WORLD);

  FILE *arq_saida = fopen("saida_paralelo.txt", "w");

  if (arq_saida == NULL) {
    perror("Error ao gravar arquivo!");
    MPI_Finalize();

    exit(1);
  }

  if (primos_final != NULL) {
    for (int i = 0; i < quantidade; i++) {
      if (primos_final[i]) {
        fprintf(arq_saida, "%d\n", i + 2);
      }
    }
  }

  liberar_memoria((void **)&primos_local);
  liberar_memoria((void **)&primos_base);
  liberar_memoria((void **)&primos_final);

  fclose(arq_saida);
  arq_saida = NULL;

  MPI_Finalize();
  return 0;
}