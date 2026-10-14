import {
  formatAmount,
  opportunityStages,
  type Summary,
  type MetricGroup,
} from "./types";
export function Results({
  title,
  items,
}: {
  title: string;
  items: MetricGroup[];
}) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <h2>{title}</h2>
      </div>
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>Naziv</th>
              <th>Prilike</th>
              <th>Otvorene</th>
              <th>Vrednost otvorenih</th>
              <th>Dobijene</th>
              <th>Vrednost dobijenih</th>
              <th>Izgubljene</th>
            </tr>
          </thead>
          <tbody>
            {items.map((row) => (
              <tr key={row.owner_id ?? row.company_id}>
                <td>{row.name}</td>
                <td>{row.opportunity_count}</td>
                <td>{row.open_count}</td>
                <td>{formatAmount(row.open_value)}</td>
                <td>{row.won_count}</td>
                <td>{formatAmount(row.won_value)}</td>
                <td>{row.lost_count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {!items.length && (
        <p className="empty">Nema rezultata za odabrane filtere.</p>
      )}
    </section>
  );
}
export default function Reports({ data }: { data: Summary }) {
  return (
    <div className="reports-panels">
      <section className="panel">
        <div className="panel-heading">
          <h2>Broj i vrednost po fazama</h2>
        </div>
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Faza</th>
                <th>Broj prilika</th>
                <th>Vrednost (RSD)</th>
              </tr>
            </thead>
            <tbody>
              {opportunityStages.map((stage) => (
                <tr key={stage}>
                  <td>{stage}</td>
                  <td>{data.stages[stage]}</td>
                  <td>{formatAmount(data.stage_values[stage])}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
      <Results title="Rezultati komercijalista" items={data.sales_results} />
      <Results title="Rezultati po kompanijama" items={data.company_results} />
      <section className="panel">
        <div className="panel-heading">
          <h2>Evidentirane konverzije između faza</h2>
        </div>
        <p className="section-hint">
          Broj različitih prilika sa direktnim prelazom / broj različitih
          prilika evidentiranih u početnoj fazi tokom perioda. Ponovljeni
          prelazi iste prilike broje se jednom; prelaz unazad nije uspešna
          prodaja.
        </p>
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Prelaz</th>
                <th>Prilike</th>
                <th>U početnoj fazi</th>
                <th>Udeo</th>
              </tr>
            </thead>
            <tbody>
              {data.transitions.map((row) => (
                <tr key={row.from_stage + row.to_stage}>
                  <td>
                    {row.from_stage} → {row.to_stage}
                  </td>
                  <td>{row.count}</td>
                  <td>{row.source_count}</td>
                  <td>{row.rate}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {!data.transitions.length && (
          <p className="empty">
            Nema evidentiranih prelaza u izabranom periodu. Nedostajuća stara
            istorija se ne rekonstruše.
          </p>
        )}
      </section>
      <section className="panel">
        <div className="panel-heading">
          <h2>Promene faza kroz vreme</h2>
        </div>
        <p className="section-hint">
          Mesečni broj evidentiranih ulazaka u fazu, uključujući kreiranje i
          ponovljene prelaze. Ovo nije istorijski prihod niti istorijska
          vrednost levka.
        </p>
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Mesec</th>
                <th>Faza</th>
                <th>Događaji</th>
              </tr>
            </thead>
            <tbody>
              {data.timeline.map((row) => (
                <tr key={row.month + row.stage}>
                  <td>{row.month}</td>
                  <td>{row.stage}</td>
                  <td>{row.count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {!data.timeline.length && (
          <p className="empty">Nema evidentiranih događaja za prikaz.</p>
        )}
      </section>
    </div>
  );
}
