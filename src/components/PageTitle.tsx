interface PageTitleProps {
  eyebrow?: string;
  title: string;
  description: string;
  action?: React.ReactNode;
}

export default function PageTitle({ eyebrow = "SOCAR ANALYTICS", title, description, action }: PageTitleProps) {
  return (
    <div className="page-title-row">
      <div>
        <div className="eyebrow"><span className="eyebrow-dot" />{eyebrow}</div>
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
      {action && <div className="page-title-action">{action}</div>}
    </div>
  );
}