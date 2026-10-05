import { Card, PageHeader } from '../../../components';

export function ForbiddenPage() {
  return (
    <Card>
      <PageHeader
        title="Access denied"
        description="You do not have access to this resource."
      />
    </Card>
  );
}
