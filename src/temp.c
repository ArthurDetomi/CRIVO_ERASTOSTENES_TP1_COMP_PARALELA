void crivo_segmentado_local(int inicio, int fim, int limite, char *primos_local,
                            char *primos_base) {

  for (int p = 2; p <= limite; p++) {

    // Só fazemos algo se 'p' for um número primo
    if (primos_base[p] == 1) {

      // 1. Como achar o primeiro múltiplo de 'p' dentro do meu intervalo?
      int primeiro_multiplo = inicio;
      int resto = inicio % p;

      // Se 'inicio' não for divisível por 'p', somamos o que falta para chegar
      // no próximo múltiplo
      if (resto != 0) {
        primeiro_multiplo = inicio + (p - resto);
      }

      // 2. Regra matemática: os múltiplos de 'p' menores que 'p*p'
      // já foram cortados por primos anteriores. E não queremos cortar o
      // próprio 'p'.
      if (primeiro_multiplo < (p * p)) {
        primeiro_multiplo = p * p;
      }

      // 3. Agora é só pular de 'p' em 'p' e cortar (marcar como 0)
      for (int multiplo = primeiro_multiplo; multiplo <= fim; multiplo += p) {
        primos_local[multiplo - inicio] = 0;
      }
    }
  }
}