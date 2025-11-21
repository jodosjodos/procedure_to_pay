import { Badge } from '@/components/ui/badge';
import { RequestStatus } from '@/types';
import { CheckCircle2, XCircle, Clock } from 'lucide-react';

interface StatusBadgeProps {
  status: RequestStatus;
}

export const StatusBadge = ({ status }: StatusBadgeProps) => {
  const config = {
    pending: {
      label: 'Pending',
      className: 'bg-pending text-pending-foreground',
      icon: Clock,
    },
    approved: {
      label: 'Approved',
      className: 'bg-approved text-approved-foreground',
      icon: CheckCircle2,
    },
    rejected: {
      label: 'Rejected',
      className: 'bg-rejected text-rejected-foreground',
      icon: XCircle,
    },
  };

  const { label, className, icon: Icon } = config[status];

  return (
    <Badge className={className}>
      <Icon className="h-3 w-3 mr-1" />
      {label}
    </Badge>
  );
};
