import { useEffect, useState } from "react";
import { getOrganizations } from "./api";

function App() {
  const [organizations, setOrganizations] = useState<any[]>([]);
  const [selectedOrganization, setSelectedOrganization] = useState("");

  useEffect(() => {
    getOrganizations()
      .then((data) => {
        setOrganizations(data);

        if (data.length > 0) {
          setSelectedOrganization(data[0].slug);
        }
      })
      .catch((error) => {
        console.error(error);
      });
  }, []);

  return (
    <div>
      <h1>AlphaRecon</h1>

      <label>
        Organization:{" "}
        <select
          value={selectedOrganization}
          onChange={(event) =>
            setSelectedOrganization(event.target.value)
          }
        >
          {organizations.map((organization) => (
            <option
              key={organization.id}
              value={organization.slug}
            >
              {organization.name}
            </option>
          ))}
        </select>
      </label>

      <p>Selected organization: {selectedOrganization}</p>
    </div>
  );
}

export default App;