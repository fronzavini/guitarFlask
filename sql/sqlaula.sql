CREATE TABLE `usuario` (
    `cod_usuario` INT AUTO_INCREMENT PRIMARY KEY, -- Código do usuário no sistema
    `nome_usuario` VARCHAR(50) COLLATE utf8mb4_general_ci DEFAULT NULL, -- Nome do usuário
    `username_usuario` VARCHAR(50) COLLATE utf8mb4_general_ci NOT NULL, -- login do usuário no sistema
    `email_usuario` VARCHAR(100) COLLATE utf8mb4_general_ci NOT NULL UNIQUE, -- Email de cadastro do usuário
    `password_usuario` VARCHAR(255) COLLATE utf8mb4_general_ci DEFAULT NULL, -- Aumentado para 255 para hashes mais longos
    `foto_usuario` VARCHAR(100), -- arquivo da imagem do usuario
    `conta_ativa` BOOLEAN NOT NULL DEFAULT TRUE, -- caso seja desejado ativar conta do usuário
    `criacao_usuario` TIMESTAMP DEFAULT CURRENT_TIMESTAMP -- Data da criação do usuário
);