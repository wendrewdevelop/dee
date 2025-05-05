# Variáveis
PREFIX ?= /usr/local
BINDIR := $(PREFIX)/bin
TARGET := deevcs
SRC := main.c

# Alvo padrão
all: $(TARGET)

# Compilação
$(TARGET): $(SRC)
	$(CC) $(CFLAGS) -o $@ $^

# Instalação
install: $(TARGET)
	install -d $(DESTDIR)$(BINDIR)
	install -m 755 $(TARGET) $(DESTDIR)$(BINDIR)/$(TARGET)

# Limpeza
clean:
	rm -f $(TARGET)
