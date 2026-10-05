import { Card, PageHeader } from '../../../components';

export function NotFoundPage() {
  return (
    <Card>
      <PageHeader title="Page not found" description="This address does not exist in the console." />
    </Card>
  );
}
