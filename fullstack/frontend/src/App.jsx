import { useEffect, useState } from "react";

const statNames = {
  hp: "HP",
  attack: "Attack",
  defense: "Defense",
  "special-attack": "Sp. Atk",
  "special-defense": "Sp. Def",
  speed: "Speed",
};
const formatName = (name) => name.replaceAll("-", " ");

function PokemonCard({ pokemon }) {
  const [imageFailed, setImageFailed] = useState(false);
  const hp = pokemon.stats.find((stat) => stat.name === "hp")?.value;

  return (
    <article
      className={`pokemon-card type-${pokemon.types[0]}`}
      aria-label={`${formatName(pokemon.name)} Pokémon card`}
    >
      <header className="card-heading">
        <h1>{formatName(pokemon.name)}</h1>
        <span className="hp">
          <small>HP</small> {hp}
        </span>
      </header>

      <div className="artwork">
        {pokemon.image && !imageFailed ? (
          <img
            src={pokemon.image}
            alt={formatName(pokemon.name)}
            onError={() => setImageFailed(true)}
          />
        ) : (
          <span>Artwork unavailable</span>
        )}
      </div>
      <p className="measurements">
        No. {String(pokemon.id).padStart(3, "0")}
        <span>Height: {pokemon.height_m.toLocaleString()} m</span>
        <span>Weight: {pokemon.weight_kg.toLocaleString()} kg</span>
      </p>

      <section className="abilities" aria-label="Abilities">
        <h2>Abilities</h2>
        <p>{pokemon.abilities.map(formatName).join(" · ")}</p>
      </section>

      <dl className="stats" aria-label="Base stats">
        {pokemon.stats.map((stat) => (
          <div key={stat.name}>
            <dt>{statNames[stat.name] || formatName(stat.name)}</dt>
            <dd>{stat.value}</dd>
          </div>
        ))}
      </dl>
      <footer className="card-footer">
        <span>{pokemon.types.join(" / ")}</span>
        <span>
          #{String(pokemon.id).padStart(3, "0")}{" "}
          <span aria-hidden="true">✦</span>
        </span>
      </footer>
    </article>
  );
}

export default function App() {
  const [input, setInput] = useState("");
  const [search, setSearch] = useState({ name: "bulbasaur" });

  /** TODO:
   *  Create a new pokemon state and set its initial value to null
   *  This will be used to store the pokemon data from the request
   */

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError("");

    async function fetchPokemon() {
      try {
        const name = encodeURIComponent(search.name);
        const response = await fetch(
          "TODO: Fetch the right API endpoint from your backend",
          { signal: controller.signal },
        );
        const data = await response.json();
        if (!response.ok)
          throw new Error(
            typeof data.detail === "string"
              ? data.detail
              : "Something went wrong. Please try again.",
          );
        setPokemon(data);
      } catch (err) {
        if (controller.signal.aborted) return;
        setError(
          err instanceof TypeError || err instanceof SyntaxError
            ? "Unable to reach the Pokédex. Check that the backend is running and try again."
            : err.message,
        );
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }

    fetchPokemon();
    return () => controller.abort();
  }, [search]);

  function submit(event) {
    event.preventDefault();
    const name = input.trim().toLowerCase();
    if (name) setSearch({ name });
  }

  return (
    <main className="app">
      <form className="search-form" onSubmit={submit}>
        <label className="sr-only" htmlFor="pokemon-search">
          Pokémon name or number. Press Enter to search.
        </label>
        <input
          id="pokemon-search"
          type="search"
          value={input}
          onChange={(event) => setInput(event.target.value)}
          placeholder="Search a Pokémon"
          enterKeyHint="search"
          autoComplete="off"
          spellCheck="false"
          maxLength={100}
          required
        />
      </form>

      <section
        className="result"
        aria-label="Search result"
        aria-busy={loading}
      >
        <div className="sr-only" role="status">
          {!loading && !error && pokemon
            ? `${formatName(pokemon.name)} loaded.`
            : ""}
        </div>
        {loading ? (
          <p className="message" role="status">
            Loading Pokémon…
          </p>
        ) : error ? (
          <p className="message error" role="alert">
            {error}
          </p>
        ) : (
          pokemon &&
          {
            /**
             *  TODO: Put the PokemonCard component here
             *  Pass it the `pokemon` object state variable
             *  as a prop
             */
          }
        )}
      </section>
    </main>
  );
}
