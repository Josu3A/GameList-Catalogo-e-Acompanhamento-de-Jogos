import { Badge } from '@mantine/core';
import type { StatusLista } from '../types';
import { STATUS_COLOR, STATUS_LISTA } from '../lib/labels';

export function StatusBadge({ status }: { status: StatusLista }) {
  return (
    <Badge color={STATUS_COLOR[status]} variant="light">
      {STATUS_LISTA[status]}
    </Badge>
  );
}
