# Shadow Realm - RPG de Plataforma

## 1. Visão Geral do Projeto

**Nome do Projeto:** Shadow Realm
**Tipo:** Jogo de Plataforma RPG
**Resumo:** Um jogo de plataforma 2D com elementos de RPG, incluindo sistema de níveis, XP, monstros, bosses e progression.
**Público-alvo:** Jogadores que enjoyem jogos de plataforma com elementos de RPG

## 2. Especificação de UI/UX

### Estrutura do Layout
- **Tela Principal:** Menu com opções (Novo Jogo, Continuar, Sair)
- **Tela de Jogo:** Área de jogo principal com HUD
- **Tela de Pause:** Menu de pause com opções
- **Tela de Batalha:** Modal de combate quando encounter com monstro
- **Tela de Game Over:** Tela de morte do personagem

### Design Visual
- **Paleta de Cores:**
  - Background: #1a1a2e (azul escuro)
  - Plataforma: #16213e (azul marinho)
  - Player: #e94560 (rosa/vemelho)
  - Monstro: #ff6b35 (laranja)
  - Boss: #7b2cbf (roxo)
  - XP/Level: #ffd700 (dourado)
  - HUD: #0f3460 (azul)
  - Texto: #ffffff (branco)
  
- **Tipografia:** 
  - Títulos: Bold, 48px
  - HUD: Regular, 20px
  - Dialogos: Regular, 16px

- **Efeitos Visuais:**
  - Partículas ao tomar dano
  - Flash ao defeat monstro
  - Animação de nível up
  - Efeito de shake na tela

### Componentes
- **Player:** Retângulo animado com direções
- **Monstro:** Sprites diferentes por tipo
- **Plataformas:** Blocos retangulares
- **Boss:** Maior e mais complexo
- **HUD:** Barra de HP, XP, nível, minimapa
- **Inventário:** Grid de itens

## 3. Especificação de Funcionalidades

### Sistema de Player
- **Movimento:** Andar (esquerda/direita), Pular, Ataque
- **Atributos:**
  - HP (vida) - máximo 100
  - MP (mana) - máximo 50
  - Ataque - base 10
  - Defesa - base 5
  - Velocidade - 5
  - Nível - começa em 1
  - XP - começa em 0

### Sistema de Níveis
- XP necessário por nível: nivel * 100
- Ao upar: +10 HP, +2 Ataque, +1 Defesa, +5 MP
- Máximo nível: 99

### Sistema de Monstros
- **Tipos:**
  - Slime (níveis 1-3) - fraco, HP 20
  - Goblin (níveis 2-5) - médio, HP 35
  - Esqueleto (níveis 4-7) - forte, HP 50
  - Orc (níveis 6-10) - muito forte, HP 80
  - Dragão (Boss nível 10) - Chefão, HP 300

### Sistema de Combates
- Turn-based quando encostar em monstro
- Opções: Atacar, Usar Item, Fugir
- Dano = (Ataque do player - Defesa do monstro) + variação aleatória
- Ao defeat: XP + (nivel_monstro * 20)

### Itens
- **Poção de Vida:** Cura 30 HP
- **Poção de Mana:** Cura 20 MP
- **Espada Melhorada:** +5 Ataque permanente
- **Armadura Melhorada:** +5 Defesa permanente

### Mapa
- Múltiplas fases/salas
- Plataformas em diferentes alturas
- Portas para próximas áreas
- Spawns aleatórios de monstros

### Saves
- Salvar posição, nível, XP, HP, inventario
- Arquivo JSON

## 4. Critérios de Aceitação

1. ✅ Player pode se mover e pular entre plataformas
2. ✅ Sistema de níveis funciona corretamente
3. ✅ Monstros aparecem e podem ser derrotados
4. ✅ Boss aparece no final
5. ✅ XP é gainado ao defeat monstros
6. ✅ Itens podem ser usados
7. ✅ Game over quando HP chega a 0
8. ✅ Jogo pode ser salvo e carregado
9. ✅ HUD mostra todas informações relevantes
10. ✅ Controles são responsivos

