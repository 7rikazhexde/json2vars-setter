{-# LANGUAGE DeriveGeneric #-}
{-# LANGUAGE OverloadedStrings #-}

-- Minimal JSON configuration parser used to demonstrate consuming the
-- json2vars-setter matrix file in a Haskell project. Parsing uses the Aeson
-- library (Haskell has no JSON parser in base); the checks are plain assertions
-- that exit non-zero on failure, so no test framework is required.
module Main (main) where

import Control.Monad (unless)
import Data.Aeson (FromJSON, decode)
import qualified Data.ByteString.Lazy.Char8 as BL
import GHC.Generics (Generic)
import System.Exit (exitFailure)

newtype Versions = Versions {haskell :: [String]}
  deriving (Generic, Show)

instance FromJSON Versions

data Config = Config
  { os :: [String],
    versions :: Versions,
    ghpages_branch :: String
  }
  deriving (Generic, Show)

instance FromJSON Config

sample :: BL.ByteString
sample =
  BL.pack $
    unlines
      [ "{",
        "  \"os\": [\"ubuntu-latest\", \"macos-latest\"],",
        "  \"versions\": { \"haskell\": [\"9.8.4\", \"9.10.1\"] },",
        "  \"ghpages_branch\": \"ghgapes\"",
        "}"
      ]

check :: Bool -> String -> IO ()
check ok msg = unless ok $ do
  putStrLn ("FAIL: " ++ msg)
  exitFailure

main :: IO ()
main = do
  config <- case decode sample :: Maybe Config of
    Nothing -> putStrLn "FAIL: the sample matrix should parse" >> exitFailure
    Just c -> return c

  check (length (os config) == 2) "os should have 2 entries"
  check ("ubuntu-latest" `elem` os config) "os should contain ubuntu-latest"
  check ("macos-latest" `elem` os config) "os should contain macos-latest"

  -- Assert structure, not specific version values, so bumping the matrix
  -- versions never requires editing this program.
  let vs = haskell (versions config)
  check (not (null vs)) "haskell versions should be a non-empty list"
  check (all (not . null) vs) "each haskell version should be a non-empty string"

  check (ghpages_branch config == "ghgapes") "ghpages_branch should match"

  case decode (BL.pack "not json") :: Maybe Config of
    Nothing -> return ()
    Just _ -> check False "invalid JSON should fail to parse"

  putStrLn "All tests passed"
