import { Link } from 'react-router-dom';

import { Card, PageHeader } from '../../../components';
import { companyUiPaths } from '../paths';

/** Unknown Company sub-path inside a valid tenant route. */
export function CompanyNotFoundPage({ tenantId }: { tenantId: string }) {
  return (
    <Card>
      <PageHeader
        title="Company page not found"
        description="This Company address does not exist."
        actions={<Link to={companyUiPaths.overview(tenantId)}>Back to Company overview</Link>}
      />
    </Card>
  );
}
