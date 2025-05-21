// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract Voting {
    struct Candidate {
        string name;
        uint voteCount;
    }

    Candidate[] public candidates;
    mapping(string => bool) public hasVoted;
    uint public candidatesCount;

    constructor(string[] memory candidateNames) {
        for (uint i = 0; i < candidateNames.length; i++) {
            candidates.push(Candidate(candidateNames[i], 0));
            candidatesCount++;
        }
    }

    function vote(string memory voterid, uint candidateIndex) public {
        require(!hasVoted[voterid], "Already voted");
        require(candidateIndex < candidatesCount, "Invalid candidate index");

        hasVoted[voterid] = true;
        candidates[candidateIndex].voteCount++;
    }

    function getCandidates() public view returns (string[] memory names) {
        names = new string[](candidatesCount);
        for (uint i = 0; i < candidatesCount; i++) {
            names[i] = candidates[i].name;
        }
    }

    function getVoteCount(uint index) public view returns (uint) {
        require(index < candidatesCount, "Invalid index");
        return candidates[index].voteCount;
    }

    function hasVotedCheck(string memory voterid) public view returns (bool) {
        return hasVoted[voterid];
    }
}
