#!/usr/bin/env bash
# Respaldo del Odoo de Lumak: base de datos + archivos adjuntos (PDF, certificados, kit).
# Los libros y soportes contables se conservan 10 años (Código de Comercio art. 60; Ley 962 de 2005 art. 28):
# este equipo no basta, copia cada mes un respaldo a un disco externo o a otra nube.
#
# Uso:       scripts/respaldo.sh                  (deja los archivos en ~/Respaldos/lumak)
# Restaurar: docker compose exec -T db createdb -U odoo lumak_restaurada
#            docker compose exec -T db pg_restore -U odoo -d lumak_restaurada < lumak-FECHA.dump
#            docker compose exec -T odoo mkdir -p /var/lib/odoo/filestore/lumak_restaurada
#            docker compose exec -T odoo tar -C /var/lib/odoo/filestore/lumak_restaurada -xzf - < filestore-FECHA.tar.gz
set -euo pipefail
cd "$(dirname "$0")/.."

destino=${LUMAK_RESPALDOS:-$HOME/Respaldos/lumak}
fecha=$(date +%F_%H%M)
mkdir -p "$destino"

docker compose exec -T db pg_dump -U odoo -Fc lumak > "$destino/lumak-$fecha.dump"
docker compose exec -T odoo tar -C /var/lib/odoo/filestore/lumak -czf - . > "$destino/filestore-$fecha.tar.gz"

# ponytail: se quedan los 30 más recientes; lo de largo plazo va en la copia mensual externa
for patron in "lumak-*.dump" "filestore-*.tar.gz"; do
  mapfile -t viejos < <(printf '%s\n' "$destino"/$patron | sort -r | tail -n +31)
  [ ${#viejos[@]} -gt 0 ] && rm -- "${viejos[@]}"
done

echo "Respaldo listo en $destino:"
du -h "$destino/lumak-$fecha.dump" "$destino/filestore-$fecha.tar.gz"

# Deja en el tablero de Odoo que el respaldo corrió (si Odoo no responde, el respaldo igual quedó)
tamano=$(du -ch "$destino/lumak-$fecha.dump" "$destino/filestore-$fecha.tar.gz" | tail -1 | cut -f1)
tamano="${tamano/K/ KB}"; tamano="${tamano/M/ MB}"; tamano="${tamano/G/ GB}"
(cd estadistica && "$HOME/.local/bin/uv" run --quiet python -m secop_estadistica avisar respaldo "$tamano") \
  || echo "No pude avisar a Odoo; el respaldo sí quedó."
