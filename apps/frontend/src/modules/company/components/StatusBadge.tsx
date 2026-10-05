import { Badge } from '../../../components';
import { statusTone } from '../vocabulary';

/** Status is communicated by text as well as tone (never colour alone). */
export function StatusBadge({ status }: { status: string }) {
  return <Badge tone={statusTone(status)}>{status}</Badge>;
}
