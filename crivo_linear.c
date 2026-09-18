#include <stdlib.h>

#include <stdio.h>

char *crivo_erastostenes(int n) {
  char *primos;

  int tamanho = n + 1;

  primos = (char *)malloc(tamanho);

  for (int i = 0; i < tamanho; i++) {
    primos[i] = 1;
  }

  primos[0] = 0;
  primos[1] = 0;

  for (int p = 2; p * p < tamanho; p++) {
    if (primos[p]) {
      for (int multiplo = p * p; multiplo < tamanho; multiplo += p) {
        primos[multiplo] = 0;
      }
    }
  }

  return primos;
}

int main(int argc, char *argv[]) {
  if (argc != 2) {
    perror("É necessário informar o valor de N como segundo argumento");
    exit(1);
  }

  int n = atoi(argv[1]);

  FILE *arq_saida = fopen("saida_linear.txt", "w");

  char *primos = crivo_erastostenes(n);

  for (int i = 0; i < n + 1; i++) {
    if (primos[i]) {
      printf("%d\n", i);
      fprintf(arq_saida, "%d\n", i);
    }
  }

  fclose(arq_saida);
  arq_saida = NULL;

  free(primos);
  primos = NULL;

  return 0;
}