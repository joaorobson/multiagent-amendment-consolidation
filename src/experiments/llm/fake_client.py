from models import StatusEmenda, EdicaoEmenda, DeliberacaoEmenda
from .prompts import PROMPT_APLICAR_EMENDAS, PROMPT_BUSCAR_EDICOES, PROMPT_EXTRAIR_EMENDAS_RELATORIO

class FakeLLMClient:
    def __init__(self, responses=None):
        self.responses = responses or {}
        self.call_count = 0

    def call(self, prompt):
        self.call_count += 1
        if prompt == PROMPT_EXTRAIR_EMENDAS_RELATORIO:
            return {
                1: DeliberacaoEmenda(
                    status=StatusEmenda.APROVADA_PARCIALMENTE,
                    justificativa="Acolhida parcialmente para incorporar rotas acessíveis e sinalização adequada, sem impor exigências gerais relativas a sanitários e demais instalações, consideradas as características de cada equipamento público.",
                ),
                2: DeliberacaoEmenda(
                    status=StatusEmenda.REJEITADA,
                    justificativa="A ampliação para estabelecimentos privados poderia comprometer a focalização dos recursos públicos e exigiria critérios adicionais de seleção e fiscalização.",
                ),
                3: DeliberacaoEmenda(
                    status=StatusEmenda.APROVADA,
                    justificativa="A priorização de Municípios de pequeno porte e localidades vulneráveis permite distribuir os recursos de forma mais equilibrada, direcionando-os às localidades com maiores necessidades.",
                ),
                4: DeliberacaoEmenda(
                    status=StatusEmenda.REJEITADA,
                    justificativa="A transferência direta e a flexibilização dos mecanismos de acompanhamento comprometeriam a definição de responsabilidades e o controle da aplicação dos recursos públicos.",
                ),
                5: DeliberacaoEmenda(
                    status=StatusEmenda.APROVADA,
                    justificativa="A divulgação de informações sobre projetos, recursos e execução fortalece a transparência, o controle social e a eficiência administrativa.",
                ),
            }

        elif prompt == PROMPT_BUSCAR_EDICOES:
            return {1: [
                EdicaoEmenda(
                    bloco_busca="""Art. 4º Poderão ser apoiadas pelo Programa as seguintes ações: 
I – reforma, recuperação e ampliação das instalações físicas; 
II – adequação das instalações elétricas, hidráulicas e sanitárias; 
III – aquisição e instalação de equipamentos destinados ao funcionamento dos espaços; 
IV – implantação de estruturas para armazenamento e conservação de produtos; 
V – melhoria das condições de limpeza e gestão de resíduos; e 
VI – implantação de soluções tecnológicas destinadas à gestão e à organização das atividades comerciais.""",
                    bloco_substituicao="""Art. 4º Poderão ser apoiadas pelo Programa as seguintes ações:
I – reforma, recuperação e ampliação das instalações físicas;
II – adequação das instalações elétricas, hidráulicas e sanitárias;
III – aquisição e instalação de equipamentos destinados ao funcionamento dos espaços;
IV – implantação de estruturas para armazenamento e conservação de produtos;
V – melhoria das condições de limpeza e gestão de resíduos; e
VI – implantação de soluções tecnológicas destinadas à gestão e à organização das atividades comerciais.
Art. 4º-A. Os projetos de modernização apoiados pelo Programa deverão contemplar medidas destinadas a garantir condições adequadas de acessibilidade às pessoas com deficiência ou mobilidade reduzida.
§ 1º As intervenções deverão observar, conforme a natureza e as características do equipamento público:
I – implantação ou adequação de rotas acessíveis nas áreas de circulação; e
II – instalação de sinalização adequada para orientação e identificação dos espaços.
§ 2º As medidas previstas neste artigo deverão ser consideradas na elaboração do plano de trabalho apresentado pelo ente federativo participante."""
                )],
                3: [EdicaoEmenda(
                    bloco_busca="""Art. 6º A seleção dos projetos observará os seguintes critérios:
I – relevância da intervenção para a melhoria da infraestrutura do equipamento público;
II – quantidade estimada de comerciantes e usuários beneficiados;
III – viabilidade técnica e financeira do projeto;
IV – capacidade de execução do ente federativo proponente; e
V – compatibilidade do projeto com as diretrizes nacionais do Programa.""",
                    bloco_substituicao="""Art. 6º A seleção dos projetos observará os seguintes critérios:
I – relevância da intervenção para a melhoria da infraestrutura do equipamento público;
II – quantidade estimada de comerciantes e usuários beneficiados;
III – viabilidade técnica e financeira do projeto;
IV – capacidade de execução do ente federativo proponente; e
V – compatibilidade do projeto com as diretrizes nacionais do Programa;
VI – prioridade para projetos apresentados por Municípios de pequeno porte e por localidades que apresentem indicadores de maior vulnerabilidade socioeconômica.
Parágrafo único. Na aplicação do critério previsto no inciso VI, deverão ser considerados, entre outros fatores, o porte populacional do Município, os indicadores sociais e econômicos disponíveis e a necessidade de recuperação da infraestrutura dos equipamentos públicos abrangidos pelo Programa."""
                )],
                5: [EdicaoEmenda(
                    bloco_busca="""Art. 9º Os entes federativos participantes deverão assegurar a adequada manutenção dos equipamentos públicos modernizados com recursos do Programa, de modo a preservar as condições de funcionamento e a finalidade das intervenções realizadas.""",
                    bloco_substituicao="""Art. 9º Os entes federativos participantes deverão assegurar a adequada manutenção dos equipamentos públicos modernizados com recursos do Programa, de modo a preservar as condições de funcionamento e a finalidade das intervenções realizadas.
Art. 9º-A. O órgão federal responsável pela coordenação do Programa deverá assegurar a transparência e a publicidade das informações relativas aos projetos apoiados.
§ 1º Deverão ser disponibilizadas, em meio eletrônico de acesso público, no mínimo, as seguintes informações:
I – identificação dos entes federativos e dos equipamentos públicos beneficiados;
II – descrição dos projetos selecionados;
III – valores dos recursos destinados a cada projeto;
IV – cronogramas previstos para execução das ações;
V – estágio de execução física e financeira dos projetos; e
VI – resultados alcançados com a implementação das intervenções.
§ 2º As informações de que trata o § 1º deverão ser atualizadas periodicamente, conforme periodicidade definida em regulamento.
§ 3º O órgão coordenador deverá elaborar e divulgar relatório anual consolidado sobre a execução do Programa, contendo informações sobre os recursos aplicados, os projetos concluídos e os resultados obtidos."""
                ),
            ]}
