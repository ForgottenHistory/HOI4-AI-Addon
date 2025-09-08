use hoi4save::{de::deserialize_vec_pair, CountryTag, Hoi4Date};
use jomini::JominiDeserialize;
use serde::Serialize;
use std::collections::HashMap;

#[derive(JominiDeserialize, Debug, Clone, Serialize)]
pub struct EnhancedHoi4Save {
    pub player: String,
    pub date: Hoi4Date,
    #[jomini(default, deserialize_with = "deserialize_vec_pair")]
    pub countries: Vec<(CountryTag, EnhancedCountry)>,
}

#[derive(JominiDeserialize, Debug, Clone, Serialize)]
pub struct EnhancedCountry {
    #[jomini(default)]
    pub stability: f64,
    #[jomini(default)]
    pub war_support: f64,
    #[jomini(default)]
    pub variables: HashMap<String, f64>,
    #[jomini(default)]
    pub politics: Option<Politics>,
    #[jomini(default)]
    pub political_power: Option<f64>,
    #[jomini(default)]
    pub army_experience: Option<f64>,
    #[jomini(default)]
    pub focus_tree: Option<String>,
    #[jomini(default)]
    pub cosmetic_tag: Option<String>,
}

#[derive(JominiDeserialize, Debug, Clone, Serialize)]
pub struct Politics {
    #[jomini(default)]
    pub ruling_party: Option<String>,
    #[jomini(default)]
    pub parties: Option<Parties>,
    #[jomini(default)]
    pub ideas: Option<Vec<String>>,
    #[jomini(default)]
    pub last_election: Option<String>,
    #[jomini(default)]
    pub elections_allowed: Option<bool>,
}

#[derive(JominiDeserialize, Debug, Clone, Serialize)]
pub struct Parties {
    #[jomini(default)]
    pub democratic: Option<Party>,
    #[jomini(default)]
    pub communism: Option<Party>,
    #[jomini(default)]
    pub fascism: Option<Party>,
    #[jomini(default)]
    pub neutrality: Option<Party>,
}

#[derive(JominiDeserialize, Debug, Clone, Serialize)]
pub struct Party {
    #[jomini(default)]
    pub popularity: Option<f64>,
    #[jomini(default)]
    pub country_leader: Option<CountryLeader>,
}

#[derive(JominiDeserialize, Debug, Clone, Serialize)]
pub struct CountryLeader {
    #[jomini(default)]
    pub ideology: Option<String>,
    // Note: character data might need special handling
}