import { AlertTriangle, Inbox, Loader2 } from 'lucide-react';
import type { ReactNode } from 'react';

export function LoadingBlock({ label = 'Loading…' }: { label?: string }) {
  return (
    <div className="flex items-center gap-2 py-12 justify-center text-fg-muted text-sm">
      <Loader2 size={16} className="animate-spin" />
      {label}
    </div>
  );
}

export function ErrorBlock({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="plate flex items-start gap-3 p-4 border-alert/30">
      <AlertTriangle size={18} className="text-alert shrink-0 mt-0.5" />
      <div className="flex-1">
        <p className="text-sm text-fg">Could not load this. {message}</p>
        {onRetry && (
          <button
            type="button"
            onClick={onRetry}
            className="mt-2 text-xs font-medium text-signal hover:text-signal-bright"
          >
            Try again
          </button>
        )}
      </div>
    </div>
  );
}

export function EmptyBlock({
  icon,
  title,
  action,
}: {
  icon?: ReactNode;
  title: string;
  action?: ReactNode;
}) {
  return (
    <div className="plate flex flex-col items-center justify-center gap-3 py-14 px-6 text-center">
      <span className="text-fg-faint">{icon ?? <Inbox size={28} />}</span>
      <p className="text-sm text-fg-muted max-w-sm">{title}</p>
      {action}
    </div>
  );
}
