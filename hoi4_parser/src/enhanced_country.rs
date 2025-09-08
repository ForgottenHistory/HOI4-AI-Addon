use hoi4save::{CountryTag, Hoi4Date};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::hash::Hash;

// We need to implement our own deserialize_vec_pair since the internal one is private
fn deserialize_vec_pair<'de, D, K, V>(deserializer: D) -> Result<Vec<(K, V)>, D::Error>
where
    D: serde::Deserializer<'de>,
    K: Deserialize<'de> + Eq + Hash,
    V: Deserialize<'de>,
{
    let map: HashMap<K, V> = HashMap::deserialize(deserializer)?;
    Ok(map.into_iter().collect())
}

#[derive(Deserialize, Debug, Clone, Serialize)]
pub struct EnhancedHoi4Save {
    pub player: String,
    pub date: Hoi4Date,
    #[serde(default, deserialize_with = "deserialize_vec_pair")]
    pub countries: Vec<(CountryTag, EnhancedCountry)>,
    #[serde(default)]
    pub fired_event_names: Vec<String>,
}

#[derive(Deserialize, Debug, Clone, Serialize)]
pub struct EnhancedCountry {
    #[serde(default)]
    pub stability: f64,
    #[serde(default)]
    pub war_support: f64,
    #[serde(default)]
    pub variables: HashMap<String, f64>,
    #[serde(default)]
    pub politics: Option<Politics>,
    #[serde(default)]
    pub focus: Option<Focus>,
}

#[derive(Deserialize, Debug, Clone, Serialize)]
pub struct Focus {
    #[serde(default)]
    pub progress: Option<f64>,
    #[serde(default)]
    pub current: Option<String>,
    #[serde(default)]
    pub paused: Option<String>,
}

#[derive(Deserialize, Debug, Clone, Serialize)]
pub struct Politics {
    #[serde(default)]
    pub ruling_party: Option<String>,
    #[serde(default)]
    pub political_power: Option<f64>,
    #[serde(default)]
    pub parties: Option<Parties>,
    #[serde(default)]
    pub ideas: Option<Vec<String>>,
    #[serde(default)]
    pub last_election: Option<String>,
    #[serde(default)]
    pub elections_allowed: Option<bool>,
}

#[derive(Deserialize, Debug, Clone, Serialize)]
pub struct Parties {
    #[serde(default)]
    pub democratic: Option<Party>,
    #[serde(default)]
    pub communism: Option<Party>,
    #[serde(default)]
    pub fascism: Option<Party>,
    #[serde(default)]
    pub neutrality: Option<Party>,
}

#[derive(Deserialize, Debug, Clone, Serialize)]
pub struct Party {
    #[serde(default)]
    pub popularity: Option<f64>,
    #[serde(default)]
    pub country_leader: Option<Vec<CountryLeader>>,
}

#[derive(Deserialize, Debug, Clone, Serialize)]
pub struct CountryLeader {
    #[serde(default)]
    pub ideology: Option<String>,
    #[serde(default)]
    pub character: Option<Character>,
}

#[derive(Deserialize, Debug, Clone, Serialize)]
pub struct Character {
    #[serde(default)]
    pub id: Option<i32>,
    #[serde(default)]
    pub r#type: Option<i32>,
}