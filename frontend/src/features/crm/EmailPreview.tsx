import { Fragment } from "react";
import { emailBlocks, type EmailPart } from "../../lib/emailFormatting";
function Line({ parts }: { parts: EmailPart[] }) {
  return <>{parts.map((part, index) => part.bold ? <strong key={index}>{part.text}</strong> : <Fragment key={index}>{part.text}</Fragment>)}</>;
}
export default function EmailPreview({ body }: { body: string }) {
  return <div className="email-preview" aria-label="Pregled formatiranog mejla">
    {emailBlocks(body).map((block, index) => block.kind === "list"
      ? <ul key={index}>{block.lines.map((line, i) => <li key={i}><Line parts={line} /></li>)}</ul>
      : <p key={index}>{block.lines.map((line, i) => <Fragment key={i}>{i > 0 && <br />}<Line parts={line} /></Fragment>)}</p>)}
  </div>;
}
