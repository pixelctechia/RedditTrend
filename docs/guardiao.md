# Script Guardião - Regras de Desenvolvimento e Manutenção

**ATENÇÃO: Este documento deve ser lido e compreendido ANTES de iniciar qualquer tarefa neste projeto.**

## 1. Leitura Obrigatória
- Todo desenvolvedor ou agente de IA deve ler este arquivo integralmente antes de propor ou executar qualquer alteração no código.
- A confirmação do entendimento destas regras é pré-requisito para o início do trabalho.

## 2. Escopo de Alteração
- **Alterar SOMENTE o que foi explicitamente solicitado.**
- Não refatore, renomeie, mova ou apague arquivos a menos que isso seja parte essencial e inseparável da tarefa solicitada.
- Melhorias de código "oportunistas" (limpeza, formatação, otimização não solicitada) são PROIBIDAS se não tiverem sido requisitadas.

## 3. Preservação do Dashboard
O Dashboard (`app.html` gerado por `execution/generate_app.py`) é o coração do sistema.
- **NÃO ALTERAR INADVERTIDAMENTE:**
    - Layout visual, cores ou estrutura CSS.
    - Lógica de rotas e navegação.
    - Estrutura de dados JSON injetada (manter Base64).
    - Lógica de renderização JavaScript (funções `render*`).
    - Funcionalidade de busca e filtros.
    - Geração de Markdown.
- Qualquer alteração necessária no dashboard deve ser cirúrgica e isolada, sem afetar o funcionamento global.

## 4. Segurança Contra Regressões
- O objetivo primário é manter o sistema funcionando como está hoje.
- Evite mudanças colaterais. Se alterar uma função utilitária, verifique todos os lugares onde ela é usada.
- Mantenha a compatibilidade com a versão atual do Python e as dependências existentes.

## 5. Boas Práticas de Engenharia
- Realize mudanças mínimas e consistentes.
- O código deve ser limpo, legível e seguro.
- Certifique-se de que injeções de dados no HTML sejam feitas via Base64 para evitar quebras de sintaxe.

## 6. Processo de Entrega
Ao finalizar qualquer tarefa, o agente/desenvolvedor deve relatar:
1.  **O que foi alterado:** Arquivos modificados e trechos específicos.
2.  **O que foi mantido intacto:** Confirmação explícita de que o dashboard e fluxos críticos permanecem inalterados (ou funcionais).

## 7. Validação e Testes
- Sempre forneça instruções claras de como validar a alteração localmente.
- **Teste Mínimo Obrigatório:**
    1.  Rodar o gerador: `python execution/generate_app.py`
    2.  Verificar saída: Sem erros de importação ou sintaxe.
    3.  Validar Dashboard: Abrir `app.html` (ou via servidor) e confirmar que os posts carregam e os menus funcionam.
