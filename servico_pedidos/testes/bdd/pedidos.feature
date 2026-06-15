# language: pt
Funcionalidade: Criação de pedidos na lanchonete
  Como atendente da lanchonete
  Quero registrar pedidos dos clientes
  Para que a cozinha possa prepará-los e o cliente seja cobrado corretamente

  Cenário: Pedido de balcão com pagamento via Pix
    Dado que o cliente "João" quer fazer um pedido no balcão
    E o pedido contém o item "X-Burguer" que custa R$20,00
    Quando o cliente paga via "pix"
    Então o pedido deve ser criado com status "recebido"
    E o total do pedido deve ser R$20,00
    E a mensagem de pagamento deve mencionar "Pix"

  Cenário: Pedido de entrega com taxa adicional
    Dado que o cliente "Maria" quer fazer um pedido de entrega
    E o pedido contém o item "Suco" que custa R$10,00
    Quando o cliente paga via "cartao"
    Então o pedido deve ser criado com status "recebido"
    E o total do pedido deve ser R$15,00

  Cenário: Avanço do status do pedido
    Dado que existe um pedido com status "recebido"
    Quando o status do pedido avança
    Então o status do pedido deve ser "preparando"

  Cenário: Pedido entregue está finalizado
    Dado que existe um pedido com status "entregue"
    Então o pedido deve estar finalizado
